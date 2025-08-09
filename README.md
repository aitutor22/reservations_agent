# Restaurant Voice Reservation Agent

AI-powered voice agent for restaurant reservations using OpenAI Realtime API.

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- OpenAI API key

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and add your OpenAI API key

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Features
- Real-time voice conversations
- Restaurant information queries
- Reservation management
- Natural language processing

## Tech Stack
- Frontend: React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Voice: OpenAI Realtime API
- Real-time: WebSockets