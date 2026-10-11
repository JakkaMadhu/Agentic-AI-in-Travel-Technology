# Deployment and CORS Configuration Guide

This document outlines the deployment architecture, CORS security configuration, and deployment procedures for both the FastAPI backend (`AgenticTravelTech`) and the React Vite frontend (`AgenticTravelTech_MobileApp`).

---

## 1. CORS Architecture & Pre-Flight Verification

Cross-Origin Resource Sharing (CORS) is configured at the gateway level in [app/main.py](file:///c:/TECHNICS_TRAINING/CODING/projects/AgenticTravelTech/app/main.py) via FastAPI `CORSMiddleware`.

### 1.1 Backend Configuration
- **Setting**: `CORS_ORIGINS` in [app/config.py](file:///c:/TECHNICS_TRAINING/CODING/projects/AgenticTravelTech/app/config.py) (controlled via `.env` or cloud environment variables).
- **Default Value**: `*` (allows cross-origin requests from any client origin while reflecting the caller origin for credential support).
- **Production Recommended**: Specify comma-separated domains:
  ```env
  CORS_ORIGINS=https://roamagent.vercel.app,https://roamagent.netlify.app,http://localhost:5173
  ```
- **Supported Headers & Methods**:
  - Methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `PATCH`
  - Headers: `Authorization`, `Content-Type`, `Accept`, `Origin`
  - Credentials: `true` (enables Bearer JWT authorization across origins)

### 1.2 Frontend Dynamic API URL
In [src/api/client.ts](file:///c:/TECHNICS_TRAINING/CODING/projects/AgenticTravelTech_MobileApp/src/api/client.ts), the API base URL is resolved dynamically:
```typescript
const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://localhost:8000';
const cleanBaseUrl = rawBaseUrl.trim().replace(/\/+$/, '');
const API_BASE_URL = cleanBaseUrl.endsWith('/api/v1') ? cleanBaseUrl : `${cleanBaseUrl}/api/v1`;
```
- In local development: Falls back automatically to `http://localhost:8000/api/v1`.
- In deployed production: Resolves the cloud backend URL set in `VITE_API_BASE_URL` (normalizing trailing slashes and ensuring `/api/v1` path integrity).

---

## 2. Deploying the Backend (FastAPI)

### Recommended Platform: Render / Railway / Google Cloud Run / Fly.io

#### Option A: Dockerfile Deployment (Recommended)
The repository contains an optimized [Dockerfile](file:///c:/TECHNICS_TRAINING/CODING/projects/AgenticTravelTech/Dockerfile) utilizing Python 3.11-slim with dynamic port binding:
```dockerfile
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

**Steps on Render / Railway**:
1. Connect your GitHub repository: `JakkaMadhu/Agentic-AI-in-Travel-Technology`.
2. Choose **Web Service**.
3. Set **Root Directory** to `.` (or select Docker runtime).
4. Configure the required **Environment Variables**:

| Variable | Description | Example / Source |
|---|---|---|
| `DATABASE_URL` | Supabase PostgreSQL URI (port 6543 pooler) | `postgresql://postgres.xxx:pass@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres` |
| `GROQ_API_KEY` | Groq Cloud API Key for LLM | `gsk_...` |
| `GROQ_MODEL` | Groq Model Name | `qwen/qwen-2.5-72b` or `qwen/qwen3.8-27b` |
| `RAPIDAPI_KEY` | RapidAPI Key for Booking.com | `4c8...` |
| `RAPIDAPI_HOST` | RapidAPI Booking.com Host | `booking-com15.p.rapidapi.com` |
| `JWT_SECRET_KEY` | 32-byte secret key for signing tokens | `production_random_secret_key_32chars` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration duration | `1440` (24 hours) |
| `CORS_ORIGINS` | Allowed frontend domains | `*` (or your Vercel frontend URL) |

5. Deploy. Once deployed, verify health at `https://<your-backend-app>.onrender.com/health`.

---

## 3. Deploying the Frontend (React + Vite)

### Recommended Platform: Vercel / Netlify / Cloudflare Pages

#### Option A: Vercel (Recommended)
1. In Vercel, click **Add New Project** and import the repository.
2. If the frontend is in a subdirectory or separate repository (`AgenticTravelTech_MobileApp`), set **Root Directory** to `AgenticTravelTech_MobileApp`.
3. Framework Preset: **Vite**.
4. Build Command: `npm run build` (outputs to `dist`).
5. Set **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://<your-deployed-backend>.onrender.com`
6. Click **Deploy**.

*Note: The included `vercel.json` and `public/_redirects` ensure that single-page client routing (SPA) rewrites all sub-paths to `index.html` without 404 errors on browser refresh.*

---

## 4. Post-Deployment Verification Checklist

1. **Backend Health Check**:
   ```bash
   curl -i https://<your-backend-url>/health
   ```
   Expected response: `HTTP/2 200 OK` with `{"status": "healthy", "database_connected": true}`.

2. **CORS Pre-Flight Verification**:
   ```bash
   curl -i -X OPTIONS https://<your-backend-url>/api/v1/trip/intent \
     -H "Origin: https://<your-frontend-url>" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: authorization, content-type"
   ```
   Verify that headers return:
   - `access-control-allow-origin: https://<your-frontend-url>`
   - `access-control-allow-credentials: true`
   - `access-control-allow-methods: ...`

3. **Frontend Integration Test**:
   - Open your deployed frontend URL in the browser.
   - Open Developer Tools -> Network tab.
   - Register or log in to a user account.
   - Verify that requests go to `https://<your-backend-url>/api/v1/...` and return `200 OK` with zero CORS errors.
