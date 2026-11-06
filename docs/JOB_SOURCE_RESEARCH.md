# Job Source Research

## 1. Greenhouse Job Board API
- **Official URL**: https://developers.greenhouse.io/job-board.html
- **Access Method**: Public REST API (`GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`)
- **Authentication**: None required for public boards.
- **Public Job Data**: Yes.
- **Restrictions**: 100 requests per 10 seconds per IP, rate limiting headers apply.
- **Implementation Approach**: HTTP GET using `httpx` to fetch job listings for configured `board_token`.

## 2. Lever Postings API
- **Official URL**: https://github.com/lever/postings-api
- **Access Method**: Public REST API (`GET https://api.lever.co/v0/postings/{site_id}?mode=json`)
- **Authentication**: None required for public postings.
- **Public Job Data**: Yes.
- **Restrictions**: Standard DDoS protection.
- **Implementation Approach**: HTTP GET using `httpx` to fetch job listings for configured `site_id`.

## 3. Ashby Job Board
- **Official URL**: https://developers.ashbyhq.com/reference/getting-started
- **Access Method**: Often implemented via GraphQL on public pages, or a dedicated `https://jobs.ashbyhq.com/api/non-user-graphql` endpoint.
- **Authentication**: Typically none required for fetching the public feed.
- **Public Job Data**: Yes.
- **Restrictions**: Internal GraphQL formats can change.
- **Implementation Approach**: Can try to emulate public POST requests for the JobBoardWithTeams operation. 

## 4. Workday
- **Official URL**: N/A (Tenant specific)
- **Access Method**: Usually `POST /wday/cxs/{tenant}/jobs` on the client side with `application/json`.
- **Authentication**: Unauthenticated for public postings, but requires strict anti-bot and session handshakes in some tenants.
- **Public Job Data**: Yes.
- **Restrictions**: Heavily protected by Akamai/Imperva in some tenants.
- **Implementation Approach**: UNSUPPORTED natively. Will mark as manual configuration or require Playwright if enabled in the future.

## 5. LinkedIn Official API
- **Official URL**: https://learn.microsoft.com/en-us/linkedin/talent/
- **Access Method**: `GET https://api.linkedin.com/v2/jobs` (Deprecated/Restricted)
- **Authentication**: Requires OAuth 2.0 and approved membership in the LinkedIn Talent Solutions or Consumer Solutions Partner Program.
- **Restrictions**: Active anti-scraping litigation and extreme technical countermeasures (e.g., Authwall, reCAPTCHA Enterprise, fingerprinting) for unauthenticated access. 
- **Implementation Approach**: AUTHORIZATION_REQUIRED. Will not implement scraping. Will document that manual user-authorized API credentials are required.
