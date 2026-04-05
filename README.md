# Customer Data Pipeline

A data pipeline with 3 Docker services:
- Flask API - Mock customer data server
- FastAPI - Data ingestion pipeline  
- PostgreSQL - Data storage

## Project Structure
```
customer-data-pipeline/
├── docker-compose.yml
├── README.md
├── mock-server/
│   ├── app.py
│   ├── data/customers.json
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/test_app.py
└── pipeline-service/
    ├── main.py
    ├── models/customer.py
    ├── services/ingestion.py
    ├── database.py
    ├── Dockerfile
    ├── requirements.txt
    └── tests/test_main.py
```

## Prerequisites
- Docker Desktop (running)
- Docker Compose
- (Optional) Git

## Quick Start

### 1. Clone this repository
```bash
git clone <repository-url>
cd customer-data-pipeline
```

### 2. Build and Start All Services
```bash
docker-compose up -d
```

### 3. Verify Services Are Running
```bash
docker-compose ps
```

### 4. Test the API Endpoints

#### Flask Mock Server (Port 5000)
```bash
# Get paginated customers
curl http://localhost:5000/api/customers?page=1&limit=5

# Get single customer
curl http://localhost:5000/api/customers/CUST001

# Health check
curl http://localhost:5000/api/health
```

#### FastAPI Pipeline Service (Port 8000)
```bash
# Ingest data from Flask to PostgreSQL
curl -X POST http://localhost:8000/api/ingest

# Get paginated customers from database
curl http://localhost:8000/api/customers?page=1&limit=5

# Get single customer from database
curl http://localhost:8000/api/customers/CUST001

# Health check
curl http://localhost:8000/api/health
```

## API Documentation

### Flask Mock Server Endpoints
- `GET /api/health` - Returns `{"status": "healthy"}`
- `GET /api/customers` - Paginated list (query params: `page`, `limit`)
- `GET /api/customers/{id}` - Single customer by ID

### FastAPI Pipeline Endpoints
- `POST /api/ingest` - Fetch all data from Flask and upsert into PostgreSQL
- `GET /api/customers` - Query paginated results from database (params: `page`, `limit`)
- `GET /api/customers/{id}` - Return single customer or 404
- `GET /api/health` - Health check

## Data Flow
1. Flask server loads customer data from `data/customers.json`
2. FastAPI service fetches all data from Flask (handles pagination)
3. Data is upserted into PostgreSQL using the dlt library
4. FastAPI serves data from PostgreSQL with pagination

## Database Schema
The customer data is stored in the `customer_data` schema with table `customers`:
- `customer_id` (VARCHAR(50), PRIMARY KEY)
- `first_name` (VARCHAR(100), NOT NULL)
- `last_name` (VARCHAR(100), NOT NULL)
- `email` (VARCHAR(255), NOT NULL)
- `phone` (VARCHAR(20))
- `address` (TEXT)
- `date_of_birth` (DATE)
- `account_balance` (DECIMAL(15,2))
- `created_at` (TIMESTAMP)

## Development

### Running Tests
```bash
# Flask tests
cd mock-server
python -m pytest tests/

# Pipeline service tests  
cd ../pipeline-service
python -m pytest tests/
```

### Rebuilding Images
```bash
docker-compose build
docker-compose up -d
```

## Environment Variables
The pipeline service requires:
- `DATABASE_URL`: postgresql://postgres:password@postgres:5432/customer_db

This is automatically set in docker-compose.yml.

## Troubleshooting
- If services fail to start, check logs with: `docker-compose logs <service-name>`
- Ensure ports 5000, 8000, and 5432 are available
- For ingestion issues, verify Flask service is accessible at http://mock-server:5000

## License
MIT
