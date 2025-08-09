import { useEffect, useRef } from 'react';
import type { AgentState } from '../types';

interface VoiceVisualizerProps {
  isRecording: boolean;
  audioLevel: number;
  agentState: AgentState;
}

const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({ 
  isRecording, 
  audioLevel, 
  agentState 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    let time = 0;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const centerX = canvas.offsetWidth / 2;
      const centerY = canvas.offsetHeight / 2;
      
      const circles = 3;
      for (let i = 0; i < circles; i++) {
        const offset = (time + i * 30) % 100;
        const scale = 1 + (offset / 100) * 0.5;
        const opacity = 1 - (offset / 100);
        
        const baseRadius = 40 + i * 20;
        const pulseAmount = isRecording ? audioLevel * 20 : agentState !== 'greeting' ? 10 : 0;
        const radius = baseRadius * scale + pulseAmount;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        
        let color;
        if (isRecording) {
          color = `rgba(239, 68, 68, ${opacity * 0.3})`;
        } else if (agentState !== 'greeting') {
          color = `rgba(59, 130, 246, ${opacity * 0.3})`;
        } else {
          color = `rgba(148, 163, 184, ${opacity * 0.2})`;
        }
        
        ctx.fillStyle = color;
        ctx.fill();
        
        ctx.strokeStyle = color.replace('0.3', '0.6').replace('0.2', '0.4');
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      
      time += 1;
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, audioLevel, agentState]);

  return (
    <div className="relative h-64 flex items-center justify-center">
      <canvas 
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
      />
      <div className="relative z-10 text-center">
        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full backdrop-blur-sm ${
          isRecording 
            ? 'bg-red-500/20 text-red-400' 
            : agentState !== 'greeting'
            ? 'bg-blue-500/20 text-blue-400'
            : 'bg-slate-600/20 text-slate-400'
        }`}>
          <span className="relative flex h-3 w-3">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              isRecording ? 'bg-red-400' : agentState !== 'greeting' ? 'bg-blue-400' : 'bg-slate-400'
            }`}></span>
            <span className={`relative inline-flex rounded-full h-3 w-3 ${
              isRecording ? 'bg-red-500' : agentState !== 'greeting' ? 'bg-blue-500' : 'bg-slate-500'
            }`}></span>
          </span>
          <span className="text-sm font-medium">
            {isRecording ? 'Listening...' : agentState !== 'greeting' ? 'Agent Speaking' : 'Ready'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default VoiceVisualizer;