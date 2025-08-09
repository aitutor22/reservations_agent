import { useEffect, useRef } from 'react';
import type { TranscriptMessage } from '../types';

interface TranscriptDisplayProps {
  transcript: TranscriptMessage[];
}

const TranscriptDisplay: React.FC<TranscriptDisplayProps> = ({ transcript }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  if (transcript.length === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 h-96 flex items-center justify-center">
        <p className="text-gray-500 text-center">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          Start a conversation by connecting and speaking
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4 text-gray-300">Conversation</h2>
      <div 
        ref={scrollRef}
        className="h-96 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent"
      >
        {transcript.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-gray-100'
              } ${!message.isFinal ? 'opacity-70 italic' : ''}`}
            >
              <div className="flex items-start gap-2">
                <span className={`text-xs font-medium ${
                  message.role === 'user' ? 'text-blue-200' : 'text-gray-400'
                }`}>
                  {message.role === 'user' ? 'You' : 'Agent'}
                </span>
                {!message.isFinal && (
                  <span className="inline-flex">
                    <span className="animate-pulse text-xs">...</span>
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm">{message.text}</p>
              <time className={`text-xs mt-1 block ${
                message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </time>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TranscriptDisplay;