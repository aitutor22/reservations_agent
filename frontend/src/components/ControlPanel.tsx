import { useState, useEffect } from 'react';
import type { ConnectionStatus } from '../types';

interface ControlPanelProps {
  isRecording: boolean;
  connectionStatus: ConnectionStatus;
  onRecordingToggle: () => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ 
  isRecording, 
  connectionStatus,
  onRecordingToggle 
}) => {
  const [mode, setMode] = useState<'push-to-talk' | 'tap-to-toggle'>('push-to-talk');
  const [isPressed, setIsPressed] = useState(false);

  useEffect(() => {
    if (mode === 'push-to-talk') {
      const handleMouseUp = () => {
        if (isPressed && isRecording) {
          setIsPressed(false);
          onRecordingToggle();
        }
      };

      const handleKeyUp = (e: KeyboardEvent) => {
        if (e.code === 'Space' && isPressed && isRecording) {
          e.preventDefault();
          setIsPressed(false);
          onRecordingToggle();
        }
      };

      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('keyup', handleKeyUp);

      return () => {
        window.removeEventListener('mouseup', handleMouseUp);
        window.removeEventListener('keyup', handleKeyUp);
      };
    }
  }, [mode, isPressed, isRecording, onRecordingToggle]);

  const handleButtonPress = () => {
    if (connectionStatus !== 'connected') return;

    if (mode === 'push-to-talk') {
      setIsPressed(true);
      if (!isRecording) {
        onRecordingToggle();
      }
    } else {
      onRecordingToggle();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.code === 'Space' && mode === 'push-to-talk' && !isPressed) {
      e.preventDefault();
      handleButtonPress();
    }
  };

  const isDisabled = connectionStatus !== 'connected';

  return (
    <div className="flex flex-col items-center space-y-4 mt-8">
      <div className="flex items-center gap-4 text-sm">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="mode"
            value="push-to-talk"
            checked={mode === 'push-to-talk'}
            onChange={() => setMode('push-to-talk')}
            className="text-blue-500"
          />
          <span className="text-gray-300">Push to Talk</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="mode"
            value="tap-to-toggle"
            checked={mode === 'tap-to-toggle'}
            onChange={() => setMode('tap-to-toggle')}
            className="text-blue-500"
          />
          <span className="text-gray-300">Tap to Toggle</span>
        </label>
      </div>

      <button
        onMouseDown={mode === 'push-to-talk' ? handleButtonPress : undefined}
        onClick={mode === 'tap-to-toggle' ? handleButtonPress : undefined}
        onKeyDown={handleKeyDown}
        disabled={isDisabled}
        className={`
          relative w-24 h-24 rounded-full transition-all duration-200 
          ${isDisabled 
            ? 'bg-gray-700 cursor-not-allowed opacity-50' 
            : isRecording 
            ? 'bg-red-500 hover:bg-red-600 scale-110 shadow-lg shadow-red-500/50' 
            : 'bg-blue-500 hover:bg-blue-600 shadow-lg shadow-blue-500/30'
          }
          ${isPressed && !isDisabled ? 'scale-95' : ''}
          flex items-center justify-center
        `}
      >
        <svg 
          className="w-10 h-10 text-white" 
          fill="currentColor" 
          viewBox="0 0 20 20"
        >
          {isRecording ? (
            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
          ) : (
            <path 
              fillRule="evenodd" 
              d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" 
              clipRule="evenodd" 
            />
          )}
        </svg>
        
        {isRecording && (
          <span className="absolute inset-0 rounded-full animate-ping bg-red-400 opacity-75"></span>
        )}
      </button>

      <div className="text-center text-sm text-gray-400">
        {isDisabled ? (
          <span>Connect to start</span>
        ) : mode === 'push-to-talk' ? (
          <span>Hold <kbd className="px-2 py-1 bg-slate-700 rounded">Space</kbd> or click to talk</span>
        ) : (
          <span>Click to {isRecording ? 'stop' : 'start'} recording</span>
        )}
      </div>
    </div>
  );
};

export default ControlPanel;