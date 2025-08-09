import { useState, useRef, useCallback, useEffect } from 'react';
import type { ConnectionStatus, TranscriptMessage, Reservation } from '../types';

interface WebSocketEvents {
  onTranscriptPartial?: (message: TranscriptMessage) => void;
  onTranscriptFinal?: (message: TranscriptMessage) => void;
  onAgentStateChange?: (state: string) => void;
  onReservationConfirmed?: (reservation: Reservation) => void;
  onAudioResponse?: (data: ArrayBuffer) => void;
  onError?: (error: string) => void;
}

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  sessionId: string | null;
  connect: () => void;
  disconnect: () => void;
  sendAudioChunk: (data: ArrayBuffer) => void;
  sendEndOfAudio: () => void;
  isConnected: boolean;
}

export const useWebSocket = (
  wsUrl: string,
  events: WebSocketEvents
): UseWebSocketReturn => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;

        ws.send(JSON.stringify({
          type: 'session:start',
          data: {
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          },
        }));
      };

      ws.onmessage = (event) => {
        if (typeof event.data === 'string') {
          try {
            const message = JSON.parse(event.data);
            handleMessage(message);
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        } else if (event.data instanceof ArrayBuffer) {
          if (events.onAudioResponse) {
            events.onAudioResponse(event.data);
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        if (events.onError) {
          events.onError('Connection error occurred');
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('idle');
        wsRef.current = null;
        setSessionId(null);

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
      if (events.onError) {
        events.onError('Failed to establish connection');
      }
    }
  }, [wsUrl, events]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    reconnectAttemptsRef.current = maxReconnectAttempts;
    
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'session:end' }));
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setConnectionStatus('idle');
    setSessionId(null);
  }, []);

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'session:created':
        setSessionId(message.data.sessionId);
        break;

      case 'transcript:partial':
        if (events.onTranscriptPartial) {
          events.onTranscriptPartial({
            id: `${Date.now()}-partial`,
            role: message.data.role,
            text: message.data.text,
            timestamp: Date.now(),
            isFinal: false,
          });
        }
        break;

      case 'transcript:final':
        if (events.onTranscriptFinal) {
          events.onTranscriptFinal({
            id: `${Date.now()}-final`,
            role: message.data.role,
            text: message.data.text,
            timestamp: Date.now(),
            isFinal: true,
          });
        }
        break;

      case 'agent:state':
        if (events.onAgentStateChange) {
          events.onAgentStateChange(message.data.state);
        }
        break;

      case 'reservation:confirmed':
        if (events.onReservationConfirmed) {
          events.onReservationConfirmed(message.data.reservation);
        }
        break;

      case 'error':
        console.error('Server error:', message.data);
        if (events.onError) {
          events.onError(message.data.message);
        }
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const sendAudioChunk = useCallback((data: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'audio:chunk',
        data: Array.from(new Uint8Array(data)),
      }));
    }
  }, []);

  const sendEndOfAudio = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'audio:end' }));
    }
  }, []);

  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    connectionStatus,
    sessionId,
    connect,
    disconnect,
    sendAudioChunk,
    sendEndOfAudio,
    isConnected: connectionStatus === 'connected',
  };
};