export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'error';
export type AgentState = 'greeting' | 'information' | 'reservation' | 'confirmation';

export interface TranscriptMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  timestamp: number;
  isFinal: boolean;
}

export interface Reservation {
  id: string;
  date: string;
  time: string;
  partySize: number;
  name: string;
  phone: string;
  email?: string;
  confirmationNumber: string;
  specialRequests?: string;
  status: 'confirmed' | 'cancelled' | 'modified';
}

export interface AudioChunk {
  data: ArrayBuffer;
  timestamp: number;
  role: 'user' | 'agent';
}

export interface AppState {
  connectionStatus: ConnectionStatus;
  sessionId: string | null;
  isRecording: boolean;
  transcript: TranscriptMessage[];
  currentAgentState: AgentState;
  pendingReservation: Partial<Reservation> | null;
  confirmedReservation: Reservation | null;
  audioLevel: number;
}