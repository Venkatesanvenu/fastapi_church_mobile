# Series API Documentation

## Overview
The Series API allows Admins to create, view, update, and delete series. All authenticated users (Admin, Teaching, Publishing, Small Groups) can view series.

## Endpoints

### Base URL
All endpoints are prefixed with `/api/v1/series`

---

### 1. Get All Series
**GET** `/api/v1/series/list`

**Access:** All authenticated users

**Response:**
```json
[
  {
    "id": "c0d020fe-4600-4cf9-a554-a594f91abf23",
    "title": "The Life of Jesus",
    "from_date": "2025-01-01",
    "to_date": "2025-01-10",
    "passage": "John 3:16",
    "description": "A 10-day devotional series on the life and teachings of Jesus.",
    "created_by_id": 1,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
]
```

---

### 2. Get Series Count
**GET** `/api/v1/series/count`

**Access:** All authenticated users

**Response:**
```json
{
  "total": 5
}
```

---

### 3. Get Series by ID
**GET** `/api/v1/series/{series_id}`

**Access:** All authenticated users

**Parameters:**
- `series_id` (path, string, UUID): The ID of the series

**Response:**
```json
{
  "id": "c0d020fe-4600-4cf9-a554-a594f91abf23",
  "title": "The Life of Jesus",
  "from_date": "2025-01-01",
  "to_date": "2025-01-10",
  "passage": "John 3:16",
  "description": "A 10-day devotional series on the life and teachings of Jesus.",
  "created_by_id": 1,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

**Error Responses:**
- `404 Not Found`: Series not found

---

### 4. Create Series
**POST** `/api/v1/series/create`

**Access:** Admin only

**Request Body:**
```json
{
  "title": "The Life of Jesus",
  "from_date": "2025-01-01",
  "to_date": "2025-01-10",
  "passage": "John 3:16",
  "description": "A 10-day devotional series on the life and teachings of Jesus."
}
```

**Required Fields:**
- `title` (string, 1-255 chars)
- `from_date` (date, YYYY-MM-DD)
- `to_date` (date, YYYY-MM-DD)
- `passage` (string, 1-255 chars)
- `description` (string, min 1 char)

**Validation:**
- `from_date` must be before or equal to `to_date`

**Response:** `201 Created`
```json
{
  "id": "c0d020fe-4600-4cf9-a554-a594f91abf23",
  "title": "The Life of Jesus",
  "from_date": "2025-01-01",
  "to_date": "2025-01-10",
  "passage": "John 3:16",
  "description": "A 10-day devotional series on the life and teachings of Jesus.",
  "created_by_id": 1,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid date range (from_date > to_date)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an Admin

---

### 5. Update Series
**PUT** `/api/v1/series/update/{series_id}`

**Access:** Admin only

**Parameters:**
- `series_id` (path, string, UUID): The ID of the series

**Request Body:** (All fields optional)
```json
{
  "title": "Updated Title",
  "from_date": "2025-01-05",
  "to_date": "2025-01-15",
  "passage": "Matthew 5:1-12",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "id": "c0d020fe-4600-4cf9-a554-a594f91abf23",
  "title": "Updated Title",
  "from_date": "2025-01-05",
  "to_date": "2025-01-15",
  "passage": "Matthew 5:1-12",
  "description": "Updated description",
  "created_by_id": 1,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-02T00:00:00"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid date range
- `404 Not Found`: Series not found
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an Admin

---

### 6. Delete Series
**DELETE** `/api/v1/series/delete/{series_id}`

**Access:** Admin only

**Parameters:**
- `series_id` (path, string, UUID): The ID of the series

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Series not found
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an Admin

---

## Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Database Migration

After adding the Series model, you need to create and run a migration:

```bash
# Create migration
alembic revision --autogenerate -m "add_series_table"

# Review the migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

---

## Example Usage

### Create a Series (Admin)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/series/create" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Life of Jesus",
    "from_date": "2025-01-01",
    "to_date": "2025-01-10",
    "passage": "John 3:16",
    "description": "A 10-day devotional series on the life and teachings of Jesus."
  }'
```

### Get All Series (Any User)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/series/list" \
  -H "Authorization: Bearer <user_token>"
```

### Update Series (Admin)
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/series/update/c0d020fe-4600-4cf9-a554-a594f91abf23" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "description": "Updated description"
  }'
```

---

## Files Created

1. **Model:** `app/models/series.py` - SQLAlchemy model with UUID primary key
2. **Schemas:** `app/schemas/series.py` - Pydantic schemas for validation
3. **Routes:** `app/routes/series.py` - FastAPI route handlers
4. **Registration:** Updated `app/main.py` to include series routes

---

## Notes

- Series IDs are UUIDs (36-character strings)
- Date validation ensures `from_date <= to_date`
- All timestamps are stored in UTC
- The `created_by_id` field tracks which admin created the series

