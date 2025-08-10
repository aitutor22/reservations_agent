# Ramen Restaurant Voice Agent - Frontend

A Vue.js 2.x voice-enabled interface for restaurant reservations using OpenAI's Realtime API via WebSocket connection to the backend.

## Overview

This frontend provides a minimalist voice-first interface with a single microphone button that enables natural conversation with the restaurant's AI assistant. The application handles real-time audio capture, PCM16 conversion, and WebSocket communication with the backend RealtimeAgent.

## Key Features

- **Voice-First Interface**: Single-button design for intuitive voice interaction
- **Real-Time Audio Processing**: PCM16 conversion at 24kHz for OpenAI compatibility
- **WebSocket Streaming**: Low-latency audio transmission to backend
- **Live Transcripts**: Real-time display of conversation
- **Gapless Audio Playback**: Smooth assistant voice responses

## Project Setup

```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:8080)
npm run serve

# Build for production
npm run build
```

## Architecture

- **Framework**: Vue.js 2.6.14 with Vuex state management
- **Audio**: Web Audio API for capture and playback
- **Communication**: WebSocket to `ws://localhost:8000/ws/realtime/agent`
- **Components**: Single VoiceInterface component (voice-only, no text chat)

## Documentation

For detailed architecture and implementation details, see:
- `/docs/frontend/llm.txt` - Comprehensive frontend architecture
- `/docs/voice_flow_architecture.md` - Full system voice flow
- `/docs/frontend/audio-streaming-fix.md` - Audio implementation details
