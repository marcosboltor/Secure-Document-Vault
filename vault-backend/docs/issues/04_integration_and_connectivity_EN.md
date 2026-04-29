# Issue 4: End-to-End Connectivity and Integration Testing

**Status**: Pending
**Priority**: High

---

## Description

Perform a comprehensive connectivity test between the frontend and backend to ensure that the infrastructure is properly integrated. This includes verifying CORS settings, database connectivity (real or mock), and unified error handling.

## Testing Scope

1. Backend: app/main.py and app/api/middlewares/cors.py
2. Frontend: Connectivity from Next.js (port 3000) to FastAPI (port 8000)
3. Database: PostgreSQL connection via SQLModel/Alembic
4. Security: Next.js 16.2.4 dependency health

---

## Testing Scenarios

### 1. Basic API Fetch

* Task: From the frontend, attempt to fetch data from GET /files.
* Expected: Return 200 OK with the mock file list.
* Verification: Check browser network tab for correct CORS headers (Access-Control-Allow-Origin).

### 2. Error Handling Integration

* Task: Request a non-existent file or send a malformed user-id header.
* Expected: Return a consistent JSON error response (404 or 422) as defined in global_handlers.py.
* Verification: Frontend should be able to parse {"status": "error", "code": "...", "message": "..."}.

### 3. Database Migration Health

* Task: Run 'uv run alembic upgrade head'.
* Expected: Database schema is successfully created/updated in the PostgreSQL instance.
* Verification: Inspect the database using a tool like pgAdmin or psql to confirm the 'files' table exists.

### 4. Binary Content Transfer

* Task: Verify that the 'encrypted_content' field is correctly received as a base64 encoded string or raw bytes in the JSON response.
* Expected: Content matches the mock data provided in FilesDatasourceImpl.

---

## Success Criteria

1. Frontend can retrieve data from the Backend without CORS errors.
2. Backend logs show incoming requests with correct CDMX timezone timestamps.
3. Database migrations complete without errors.
4. All 90 initial vulnerabilities remain resolved (audit report is clean).

---

## Instructions for Execution

1. Start Backend: uv run uvicorn app.main:app --reload
2. Start Frontend: npm run dev
3. Open Browser: http://localhost:3000
4. Check Console: Verify fetch requests to http://localhost:8000
