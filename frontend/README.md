# SafetyLens Frontend

Operator dashboard for camera evidence, incident review, procedure-grounded response plans, human approvals, and reports.

See the repository root [README.md](../README.md) for complete setup and current limitations.

## Quick start

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000/monitor. In PowerShell use `Copy-Item .env.example .env.local` instead of `cp`. Preserve an existing environment file.

`NEXT_PUBLIC_API_URL` points to the FastAPI server. `NEXT_PUBLIC_DEMO_FALLBACK=true` enables seeded display data when supported API reads fail; it does not make backend workflows or video analysis available offline. The local Camo detector opens its own preview window; it is not streamed into the browser automatically.

## Scripts

```bash
npm run dev
npm run build
npm run start
npm run lint
npm run typecheck
```
