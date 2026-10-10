# Database Schema Design

## Overview
The Agentic Travel Tech database schema is designed for a production-grade AI travel planning application. It handles user management, session tracking for the AI orchestration workflow (Phase 1 & 2), and system auditing for external API interactions.

## Tables

### 1. `users`
Manages user accounts for the mobile application.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Internal unique identifier. |
| `email` | String | Unique, Indexed, Not Null | User's email address. |
| `password_hash` | String | Not Null | Hashed password for authentication. |
| `created_at` | DateTime | Not Null, Default: now() | Timestamp of account creation. |

### 2. `trip_sessions`
The core table representing a single AI planning interaction flow.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Internal unique identifier. |
| `user_id` | Integer | Foreign Key (`users.id`) | The user who initiated the trip. |
| `session_uuid` | String | Unique, Indexed, Not Null | Client-provided UUID for tracking the session. |
| `user_query` | Text | Not Null | The raw natural language input provided by the user. |
| `status` | String | Not Null, Default: 'PENDING' | Workflow state (`PENDING`, `INTENT_PARSED`, `USER_CONFIRMED`, `PLAN_GENERATED`, `FAILED`). |
| `parsed_intent`| JSONB | Nullable | Structured JSON containing trip parameters and budget breakdown (Phase 1 output). |
| `final_plan` | JSONB | Nullable | Structured JSON containing the finalized itinerary (Phase 2 output). |
| `created_at` | DateTime | Not Null, Default: now() | Timestamp of session creation. |
| `updated_at` | DateTime | Not Null, Default: now() | Timestamp of the last update. |

### 3. `api_logs`
Tracks external interactions (Groq LLM, external travel APIs) for debugging, performance monitoring, and cost tracking.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Internal unique identifier. |
| `session_id` | Integer | Foreign Key (`trip_sessions.id`) | The session this API call belongs to. |
| `service_name` | String | Indexed, Not Null | Name of the external service (e.g., 'groq_llm', 'makemytrip_bus'). |
| `endpoint` | String | Not Null | The specific endpoint or model called. |
| `request_payload` | JSONB | Nullable | The data sent to the service. |
| `response_payload` | JSONB | Nullable | The data received from the service. |
| `status_code` | Integer | Not Null | HTTP status code of the response. |
| `latency_ms` | Integer | Not Null | Request duration in milliseconds. |
| `created_at` | DateTime | Not Null, Default: now() | Timestamp of the log entry. |

## Design Decisions
- **JSONB for Unstructured Payloads:** `parsed_intent`, `final_plan`, and API payloads use `JSONB`. The AI agents and external travel APIs return highly nested, evolving structures. Relational expansion would cause rigid schema migrations every time an API changes.
- **Auditability:** The `api_logs` table ensures that if the LLM hallucinates or an external API fails, developers can trace exactly what went wrong for a specific `trip_session` and monitor system costs.
