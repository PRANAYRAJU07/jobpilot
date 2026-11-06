# Phase 16 — Frontend Current State (Pre-Execution)

This document was created upon inspecting the repository at the start of Phase 16.

## 1. Existing Frontend Routes
- `/login`, `/register` (Auth)
- `/dashboard`
- `/jobs`, `/jobs/[id]`
- `/applications`, `/applications/[id]`
- `/activity`
- `/gmail`
- `/notifications`
- `/profile`
- `/settings`

## 2. Existing Components
- `Sidebar.tsx` (Basic static navigation)
- `StatCard.tsx` (Simple dashboard stats block)
- `StatusBadge.tsx` (Color formatter for statuses)

## 3. Existing API Client
- Uses `axios` with interceptors (adding JWT token) configured in `lib/api/client.ts`
- Handful of basic endpoints existed for `jobs.ts`, `applications.ts`, `auth.ts` but lacked full types, search params, and newer backend routes like profile editing.

## 4. Existing Authentication
- Next.js frontend has basic JWT token storage in `localStorage`
- Backend `auth_router.py` returns Bearer tokens

## 5. Existing WebSocket
- Frontend dashboard had a basic WebSocket connection to `ws://localhost:8001/ws`

## 6. Backend Endpoints Available
- `GET /api/jobs/` (No search, no pagination)
- `GET /api/applications/`
- `GET /api/sources/`
- `GET /api/profile/`
- `GET /api/notifications`
- `GET /api/gmail/connection`
- Auth routes

## 7. Backend Endpoints Missing (That need to be built)
- `GET /api/jobs/{id}/why` (For the evidence view)
- Search, filtering, and pagination parameters in `GET /api/jobs/`
- Dashboard stats aggregation endpoint `GET /api/jobs/stats`

## Conclusion
The backend is largely feature-complete for serving data, but the frontend was composed mostly of boilerplate stubs. The frontend requires a complete rebuild using real API data for every page.
