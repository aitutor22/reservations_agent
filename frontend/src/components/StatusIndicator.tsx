import { useState, useEffect } from 'react';
import type { ConnectionStatus } from '../types';

interface StatusIndicatorProps {
  connectionStatus: ConnectionStatus;
  onConnectionToggle: () => void;
  latency?: number;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ 
  connectionStatus,
  onConnectionToggle,
  latency = 0 
}) => {
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  useEffect(() => {
    if (connectionStatus === 'error') {
      const timer = setTimeout(() => {
        setReconnectAttempts(prev => prev + 1);
        onConnectionToggle();
      }, 3000);
      return () => clearTimeout(timer);
    } else if (connectionStatus === 'connected') {
      setReconnectAttempts(0);
    }
  }, [connectionStatus, onConnectionToggle]);

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return `Connection Error ${reconnectAttempts > 0 ? `(Retry ${reconnectAttempts})` : ''}`;
      default:
        return 'Disconnected';
    }
  };

  const getLatencyColor = () => {
    if (latency < 100) return 'text-green-400';
    if (latency < 300) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="flex items-center justify-between bg-slate-800/50 backdrop-blur rounded-lg px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            {connectionStatus === 'connecting' && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
            )}
            <span className={`relative inline-flex rounded-full h-3 w-3 ${getStatusColor()}`}></span>
          </span>
          <span className="text-sm font-medium text-gray-300">
            {getStatusText()}
          </span>
        </div>

        {connectionStatus === 'connected' && latency > 0 && (
          <div className="flex items-center gap-1 text-sm">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className={getLatencyColor()}>{latency}ms</span>
          </div>
        )}
      </div>

      <button
        onClick={onConnectionToggle}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          connectionStatus === 'idle' 
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : connectionStatus === 'connected'
            ? 'bg-red-600 hover:bg-red-700 text-white'
            : 'bg-gray-600 text-gray-400 cursor-not-allowed'
        }`}
        disabled={connectionStatus === 'connecting'}
      >
        {connectionStatus === 'idle' ? 'Connect' : connectionStatus === 'connected' ? 'Disconnect' : 'Connecting...'}
      </button>
    </div>
  );
};

export default StatusIndicator;