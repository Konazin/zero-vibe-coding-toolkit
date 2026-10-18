# Backend engineering profile

Use for Spring Boot Java, Python FastAPI/Django, Express, and service/API development. Existing architectural boundaries and runtime conventions take precedence.

## Domain and API contract

- Trace request -> authn/authz -> validation -> business service -> persistence -> response.
- Prefer explicit interfaces, cohesive modules, stable transaction boundaries, and domain invariants.
- Specify request/response contracts, status codes, error schemas, idempotency and retries when applicable.
- Validate input at the edge; enforce authorization at the resource, not just route or UI.
- Avoid leaking secrets or sensitive customer data to logs, traces, tests, LLMs or error responses.
- Database migration must be reversible or have an explicit rollback strategy. Do not silently alter production data.
- Preserve backwards compatibility unless the task explicitly authorizes a breaking change.

## Delivery gates

- Run relevant unit tests, integration tests with realistic persistence, contract tests and static checks supported by the project.
- Add regression tests for authorization, boundary conditions, failures, concurrency, retries, and precision when relevant.
- Validate negative paths; a 200 response test is not sufficient evidence of a correct API.
- Document the operational impact: schema, configs, metrics, recovery, data protection and deployment.

## Context budget

Read a route/controller, relevant DTO, service and repository symbols before whole directories. Prefer Graphify call/impact queries for unfamiliar modules; verify inferred edges against source and tests.
