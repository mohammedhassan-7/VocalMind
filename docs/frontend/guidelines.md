# Frontend Development Guidelines

## Package Management

This project uses **pnpm v10+**. 
- **DO NOT** use `npm` or `yarn` as it will break the `pnpm-lock.yaml` and cause CI failures.
- To install dependencies, run `pnpm install` in the `frontend` directory.

## Testing Strategy

### Unit & Integration (Vitest)
Unit tests for components and services are located in `src/tests/`.
Run them with:
```bash
pnpm run test
```

### End-to-End (Cypress)
E2E tests cover critical user journeys. They are located in `cypress/e2e/`.
Run them with:
```bash
# In one terminal, start the app in preview mode
pnpm run build && pnpm run preview
# In another terminal
pnpm run cy:run
```

### Code Coverage
We use `babel-plugin-istanbul` for instrumentation. To generate a full coverage report:
```bash
# From repository root
make fe-e2e-cov
```

This generates an HTML report in `frontend/coverage/index.html`.

## Performance
- Avoid large chunks by using `manualChunks` in `vite.config.ts`.
- Ensure all images are optimized or served via CDN.
