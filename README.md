# Geo Ingestion Starter (FastAPI + PostGIS) — Candidate Task

**Vaibhav's Take-Home Implementation**

## Overview

A FastAPI service using PostGIS for basic geospatial tasks. Implements point storage, 500m buffer processing, and spatial queries with real-world geographic accuracy.

## Setup & Run

```bash
# Clean environment
docker compose down --rmi all -v
docker compose up --build -d

# Run database migrations
docker compose run --rm --workdir /app api alembic upgrade head

# Verify everything works (2 smoke tests + 2 unit tests)
docker compose exec --workdir / api pytest tests/
```

## API Usage

### Health Check
```bash
curl localhost:8000/healthz
# Returns: {"status": "ok"}
```

### Create Feature
```bash
curl -X POST localhost:8000/features \
  -H "Content-Type: application/json" \
  -d '{"name": "Site A", "lat": 45.5017, "lon": -73.5673}'
# Returns: {"id": "uuid"}
```

### Process Feature (500m Buffer)
```bash
curl -X POST localhost:8000/features/{id}/process
# Returns: {"processed": true}
# Creates 500m buffer and calculates area (~785,398 m²)
```

### Get Feature Status
```bash
curl localhost:8000/features/{id}
# Returns: {"id": "uuid", "name": "Site A", "status": "done", "buffer_area_m2": 785398.16}
```

### Find Nearby Features
```bash
curl "localhost:8000/features/near?lat=45.5017&lon=-73.5673&radius_m=1000"
# Returns: [{"id": "uuid", "name": "Site A", "distance_m": 0.0}]
```

### Postman Collection
A comprehensive Postman collection is provided in `/postman/geo-ingestion-api.postman_collection.json`. Import this into Postman to test all API endpoints interactively with pre-configured test assertions. Or you can run it via newman as below.

```bash
docker compose --profile test run --rm newman
```

## Implementation Details

### Database Schema
- **features**: Stores named points with `geography(Point,4326)` for WGS84 coordinates
- **footprints**: Stores processed 500m buffers with calculated areas
- **GIST indexes**: Spatial indexing for performance

### PostGIS Operations
- `ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography` - Point creation
- `ST_Buffer(geom, 500)` - 500m radius buffer
- `ST_Area(geom)` - Area calculation in square meters
- `ST_DWithin(geom1, geom2, radius)` - Proximity queries

### Architecture
- **API Layer**: FastAPI routes with Pydantic validation
- **Service Layer**: PostGIS spatial operations using raw SQL
- **Data Layer**: SQLAlchemy models with geography types
- **Migrations**: Alembic for schema management

## Testing

```bash
# Run all tests
docker compose exec --workdir / api pytest tests/ -v

# Integration tests (smoke test)
docker compose exec --workdir / api pytest tests/test_smoke.py -v

# Unit tests
docker compose exec --workdir / api pytest tests/test_unit.py -v
```

## Trade-offs & Decisions

### Geography vs Geometry
**Choice**: Used `geography(Point,4326)` instead of `geometry`  
**Rationale**: Accurate real-world distance/area calculations essential for spatial applications  
**Trade-off**: Slightly slower than planar geometry, but correctness prioritized

### Raw SQL for Spatial Operations
**Choice**: Direct PostGIS function calls in service layer  
**Rationale**: Full control over spatial queries, leverage PostGIS capabilities  
**Trade-off**: Less ORM abstraction, but better spatial performance

### Route Ordering
**Choice**: `/features/near` defined before `/features/{id}`  
**Rationale**: FastAPI route matching requires specific routes before parameterized ones  
**Trade-off**: Order dependency, but necessary for correct routing

## Key Features Implemented

- PostGIS extension enabled in migration
- Geography columns with GIST spatial indexes
- Point insertion with coordinate validation
- 500m buffer processing with area calculation
- Spatial proximity queries using ST_DWithin
- Proper error handling and HTTP status codes
- Health/readiness endpoints for ops

## Production Considerations

- Spatial indexes enable fast queries on large datasets
- Geography type provides meter-accurate calculations globally
- Input validation prevents invalid coordinates
- Database transactions ensure data consistency
- Container-ready with environment configuration

---

**Status**: All requirements implemented and tests passing.