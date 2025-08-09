import { useState, useCallback, useEffect } from 'react';
import VoiceVisualizer from './components/VoiceVisualizer';
import ControlPanel from './components/ControlPanel';
import TranscriptDisplay from './components/TranscriptDisplay';
import StatusIndicator from './components/StatusIndicator';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useWebSocket } from './hooks/useWebSocket';
import type { AppState, TranscriptMessage, Reservation } from './types';
import './App.css';

function App() {
  const [appState, setAppState] = useState<AppState>({
    connectionStatus: 'idle',
    sessionId: null,
    isRecording: false,
    transcript: [],
    currentAgentState: 'greeting',
    pendingReservation: null,
    confirmedReservation: null,
    audioLevel: 0,
  });

  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/audio';

  const handleTranscriptPartial = useCallback((message: TranscriptMessage) => {
    setAppState(prev => {
      const existingIndex = prev.transcript.findIndex(
        m => !m.isFinal && m.role === message.role
      );
      
      if (existingIndex >= 0) {
        const newTranscript = [...prev.transcript];
        newTranscript[existingIndex] = message;
        return { ...prev, transcript: newTranscript };
      }
      
      return { ...prev, transcript: [...prev.transcript, message] };
    });
  }, []);

  const handleTranscriptFinal = useCallback((message: TranscriptMessage) => {
    setAppState(prev => {
      const filteredTranscript = prev.transcript.filter(
        m => m.isFinal || m.role !== message.role
      );
      return { ...prev, transcript: [...filteredTranscript, message] };
    });
  }, []);

  const handleAgentStateChange = useCallback((state: string) => {
    setAppState(prev => ({ 
      ...prev, 
      currentAgentState: state as AppState['currentAgentState'] 
    }));
  }, []);

  const handleReservationConfirmed = useCallback((reservation: Reservation) => {
    setAppState(prev => ({ 
      ...prev, 
      confirmedReservation: reservation,
      pendingReservation: null 
    }));
  }, []);

  const handleError = useCallback((error: string) => {
    console.error('WebSocket error:', error);
    if (error.includes('microphone') || error.includes('audio')) {
      alert('Microphone access is required for voice interaction. Please check your browser permissions.');
    }
  }, []);

  const ws = useWebSocket(wsUrl, {
    onTranscriptPartial: handleTranscriptPartial,
    onTranscriptFinal: handleTranscriptFinal,
    onAgentStateChange: handleAgentStateChange,
    onReservationConfirmed: handleReservationConfirmed,
    onError: handleError,
  });

  const handleAudioData = useCallback((data: ArrayBuffer) => {
    if (ws.isConnected) {
      ws.sendAudioChunk(data);
    }
  }, [ws]);

  const { 
    isRecording, 
    audioLevel, 
    startRecording, 
    stopRecording,
    error: audioError 
  } = useAudioRecorder(handleAudioData);

  useEffect(() => {
    setAppState(prev => ({ 
      ...prev, 
      connectionStatus: ws.connectionStatus,
      sessionId: ws.sessionId 
    }));
  }, [ws.connectionStatus, ws.sessionId]);

  useEffect(() => {
    setAppState(prev => ({ 
      ...prev, 
      isRecording,
      audioLevel 
    }));
  }, [isRecording, audioLevel]);

  const handleRecordingToggle = async () => {
    if (!ws.isConnected) {
      alert('Please connect first before recording');
      return;
    }

    if (isRecording) {
      stopRecording();
      ws.sendEndOfAudio();
    } else {
      try {
        await startRecording();
      } catch (error) {
        console.error('Failed to start recording:', error);
        alert('Failed to access microphone. Please check your permissions.');
      }
    }
  };

  const handleConnectionToggle = () => {
    if (ws.connectionStatus === 'idle') {
      ws.connect();
    } else if (ws.connectionStatus === 'connected') {
      if (isRecording) {
        stopRecording();
      }
      ws.disconnect();
      setAppState(prev => ({ 
        ...prev, 
        transcript: [],
        confirmedReservation: null,
        pendingReservation: null 
      }));
    }
  };

  useEffect(() => {
    if (audioError) {
      alert(`Audio Error: ${audioError}`);
    }
  }, [audioError]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            The Garden Bistro
          </h1>
          <p className="text-gray-400">AI-Powered Voice Reservation Assistant</p>
        </header>

        <div className="max-w-4xl mx-auto space-y-6">
          <StatusIndicator 
            connectionStatus={appState.connectionStatus}
            onConnectionToggle={handleConnectionToggle}
            latency={ws.isConnected ? 50 : undefined}
          />

          <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-8 shadow-2xl border border-slate-700/50">
            <VoiceVisualizer 
              isRecording={appState.isRecording}
              audioLevel={appState.audioLevel}
              agentState={appState.currentAgentState}
            />

            <ControlPanel
              isRecording={appState.isRecording}
              connectionStatus={appState.connectionStatus}
              onRecordingToggle={handleRecordingToggle}
            />
          </div>

          <TranscriptDisplay transcript={appState.transcript} />

          {appState.confirmedReservation && (
            <div className="bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-500/50 rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <svg className="w-6 h-6 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <h3 className="text-xl font-semibold text-green-400">Reservation Confirmed</h3>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Confirmation #:</span>
                  <p className="font-mono text-white">{appState.confirmedReservation.confirmationNumber}</p>
                </div>
                <div>
                  <span className="text-gray-400">Date:</span>
                  <p className="text-white">{appState.confirmedReservation.date}</p>
                </div>
                <div>
                  <span className="text-gray-400">Time:</span>
                  <p className="text-white">{appState.confirmedReservation.time}</p>
                </div>
                <div>
                  <span className="text-gray-400">Party Size:</span>
                  <p className="text-white">{appState.confirmedReservation.partySize} guests</p>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-400">Name:</span>
                  <p className="text-white">{appState.confirmedReservation.name}</p>
                </div>
                {appState.confirmedReservation.specialRequests && (
                  <div className="col-span-2">
                    <span className="text-gray-400">Special Requests:</span>
                    <p className="text-white">{appState.confirmedReservation.specialRequests}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <footer className="text-center mt-12 text-gray-500 text-sm">
          <p>Powered by OpenAI Realtime API</p>
        </footer>
      </div>
    </div>
  );
}

export default App;