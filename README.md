# Smart Shortner

A production-oriented link infrastructure platform built with FastAPI, PostgreSQL, and asynchronous SQLAlchemy.

The project is being developed as a foundation for a modern URL shortener with link management, redirects, click tracking, and analytics.

## Current Features

- Create shortened links with custom short codes
- Validate destination URLs
- Detect duplicate short codes
- Redirect short links to their destination
- Enable or disable links
- Support link expiration
- Record click events
- Capture request metadata:
  - IP address
  - User-Agent
  - Referrer
- Retrieve basic click analytics
- PostgreSQL persistence
- Versioned database migrations with Alembic
- Async database access
- Automated API and integration tests
- Ruff linting and formatting

## Architecture

The backend follows a layered architecture:

```text
HTTP Request
     ↓
FastAPI API Layer
     ↓
Service Layer
     ↓
Repository Layer
     ↓
SQLAlchemy AsyncSession
     ↓
PostgreSQL
```

Database schema changes are managed separately through Alembic:

```text
SQLAlchemy Models
       ↓
Base.metadata
       ↓
Alembic Migration
       ↓
PostgreSQL Schema
```

### Main responsibilities

**API Layer**
- Handles HTTP requests and responses
- Validates request data
- Converts application errors into HTTP responses

**Service Layer**
- Contains business logic
- Determines whether a link can be resolved
- Coordinates link creation and click tracking

**Repository Layer**
- Encapsulates database queries
- Keeps persistence logic separate from business logic

**Models**
- Define the PostgreSQL database structure using SQLAlchemy ORM

**Schemas**
- Define API input/output contracts using Pydantic

## Tech Stack

- **Python 3.13**
- **FastAPI**
- **SQLAlchemy 2.0**
- **asyncpg**
- **PostgreSQL 15+**
- **Alembic**
- **Pydantic**
- **pytest**
- **pytest-asyncio**
- **httpx**
- **Ruff**

## Project Structure

```text
app/
├── api/
│   ├── redirects.py
│   └── v1/
│       ├── links.py
│       └── router.py
├── core/
│   ├── config.py
│   └── database.py
├── models/
│   ├── base.py
│   ├── link.py
│   └── click_event.py
├── repositories/
│   ├── link.py
│   └── click_event.py
├── schemas/
│   └── link.py
├── services/
│   └── link.py
└── main.py

alembic/
├── versions/
└── env.py

tests/
├── conftest.py
└── test_links.py
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/kapilraghav2801/URL-Shortner.git
cd URL-Shortner
```

### 2. Create a virtual environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```


### 3. Install dependencies

```bash
python -m pip install -e ".[dev]"
```

### 4. Configure PostgreSQL

Create a PostgreSQL database named:

```text
url_shortner
```

Then create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/url_shortner
```

Do not commit `.env` to Git.

### 5. Apply database migrations

```bash
alembic upgrade head
```

## Running the API

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

## API Endpoints

### Create a link

```text
POST /api/v1/links
```

Request:

```json
{
  "destination_url": "https://example.com",
  "short_code": "example"
}
```

### Redirect

```text
GET /{short_code}
```

Example:

```text
GET /example
```

The request is redirected to the configured destination URL and a click event is recorded.

### Analytics

```text
GET /api/v1/links/{short_code}/analytics
```

Example response:

```json
{
  "short_code": "example",
  "total_clicks": 5
}
```

## Testing

The project uses a dedicated PostgreSQL test database.

Create the test database:

```text
url_shortner_test
```

Apply migrations:

```bash
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/url_shortner_test alembic upgrade head
```

Run the test suite:

```bash
pytest -v
```

Current tests cover:

- Link creation
- Duplicate short codes
- URL validation
- Redirects
- Missing links
- Click event recording
- Inactive links
- Expired links
- Click counting
- Analytics
- Analytics for missing links

## Code Quality

Run Ruff linting:

```bash
ruff check .
```

Check formatting:

```bash
ruff format --check .
```

Format the project:

```bash
ruff format .
```

## Roadmap

The current implementation focuses on the core link infrastructure.

Planned capabilities include:

- Authentication and user accounts
- Link management dashboard
- Advanced analytics
- Time-series click analytics
- Geographic and device insights
- Rate limiting
- Caching
- QR code generation
- Custom domains
- High-throughput event processing
- Additional link intelligence capabilities

## License
MIT
