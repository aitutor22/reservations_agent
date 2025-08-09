# Backend TODO List - PostgreSQL Reservation System

## 1. Database Setup
- [x] Add PostgreSQL dependencies to requirements.txt (sqlalchemy, asyncpg, alembic, psycopg2-binary)
- [x] Create database.py for connection configuration
- [x] Set up SQLAlchemy async engine and session management
- [x] Add connection pooling configuration
- [x] Configure DATABASE_URL environment variable

## 2. Models
- [x] Create Pydantic reservation model in models/reservation.py
  - phone_number (str, primary key, e.g., "+6598207272")
  - name (str)
  - reservation_date (str, ISO format)
  - reservation_time (str, HH:MM format)
  - party_size (int)
  - other_info (Optional[dict])
- [x] Create SQLAlchemy reservation model in models/db_models.py
- [x] Add timestamps (created_at, updated_at)
- [x] Add validation for phone number format

## 3. Service Layer
- [x] Create services/reservation_service.py with async CRUD operations
- [x] Implement create_reservation()
- [x] Implement get_reservation_by_phone()
- [x] Implement update_reservation()
- [x] Implement delete_reservation()
- [x] Implement list_all_reservations() with pagination
- [x] Add proper error handling and logging

## 4. API Endpoints
- [x] POST /api/reservations - Create new reservation
- [x] GET /api/reservations/{phone_number} - Get reservation by phone
- [x] PUT /api/reservations/{phone_number} - Update reservation
- [x] DELETE /api/reservations/{phone_number} - Cancel reservation
- [x] GET /api/reservations - List all reservations (admin)
- [x] Add request/response validation with Pydantic

## 5. WebSocket Integration
- [ ] Update websocket_handler.py to call reservation service for reservation commands
- [ ] Parse reservation-related messages from voice agent
- [ ] Implement real-time reservation creation via WebSocket
- [ ] Send confirmation messages back to frontend
- [ ] Handle reservation lookup requests

## 6. Database Management
- [x] Create database initialization in database.py
- [x] Set up Alembic for database migrations
- [x] Configure Alembic for async SQLAlchemy
- [ ] **USER ACTION REQUIRED**: Create initial migration: `alembic revision --autogenerate -m "Add reservation table"`
- [ ] **USER ACTION REQUIRED**: Apply migrations: `alembic upgrade head`
- [ ] Add seed data script for development/testing

## 7. Configuration
- [x] Add DATABASE_URL to .env.example
- [x] Update config.py with database configuration settings
- [x] Add database initialization on startup
- [x] Configure database pool settings
- [x] Add database health check to startup

## 8. Testing
- [ ] Unit tests for reservation service methods
- [ ] Integration tests for API endpoints
- [ ] WebSocket reservation flow tests
- [ ] Database transaction tests
- [ ] Error handling tests

## 9. Documentation
- [ ] Update API documentation with reservation endpoints
- [ ] Document WebSocket message formats for reservations
- [ ] Add database schema documentation
- [ ] Create setup instructions for PostgreSQL

## Notes
- Keep it simple for MVP - no table/availability modeling initially
- Phone number is unique (one reservation per person at a time)
- Focus on low latency for voice interactions (<50ms query time)
- Use connection pooling for concurrent requests
- Ensure proper async/await usage throughout