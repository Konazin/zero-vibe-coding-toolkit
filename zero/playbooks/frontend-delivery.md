# Frontend delivery: a practical gate matrix

## Before edits

Define acceptance behavior for all UI states: loading, empty, success, invalid input, API failure and authorization failure. Inspect established design tokens and API clients. Map affected component consumers with Graphify if the repository is complex.

## During implementation

- Preserve semantic HTML, keyboard interaction, focus visibility and reduced-motion support.
- Prefer reusable components without inventing premature abstractions.
- Avoid direct DOM manipulation that conflicts with Vue/React state ownership.
- Keep async effects cancellable and errors visible to users.
- Check error boundaries, XSS exposure, unsafe URLs and frontend-only permission assumptions.

## Gates, depending on actual stack

```bash
# Vite + Vue/React examples, only when scripts exist:
npm run lint
npm run typecheck
npm run test
npm run build
# Browser smoke, only if configured:
npx playwright test
```

Record unconfigured commands as NOT RUN. Browser screenshots do not prove keyboard access or backend authorization. Test at least mobile and desktop supported widths and one network/error path.
