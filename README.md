# Trellis

A modern monorepo with Next.js, Tailwind CSS, and TypeScript.

## Structure

```
trellis/
├── apps/
│   ├── api/                 # FastAPI service
│   └── web/                 # Next.js application
├── packages/
│   ├── ui/                  # Shared UI components
│   ├── utils/               # Utility functions
│   └── types/               # Shared TypeScript types
├── package.json             # Root package.json with workspaces
├── turbo.json              # Turbo configuration
└── tsconfig.json           # Root TypeScript configuration
```

## Getting Started (no Docker)

1. Install JavaScript dependencies:

   ```bash
   npm install
   ```

2. Install API dependencies:

   ```bash
   pip install -r apps/api/requirements.txt
   ```

3. Copy environment templates and add your Supabase project settings:

   ```bash
   cp apps/api/.env.example apps/api/.env
   cp apps/web/.env.example apps/web/.env.local
   ```

   Set `DATABASE_URL`, `SUPABASE_URL`, and the Supabase keys to match your project. The API reads the service role key; the web app uses the anon key.

4. Run the API (terminal 1):

   ```bash
   cd apps/api
   uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
   ```

5. Run the web app (terminal 2):

   ```bash
   npm run dev
   ```

6. Build all packages (optional):
   ```bash
   npm run build
   ```

## Available Scripts

- `npm run dev` - Start all development servers
- `npm run build` - Build all packages and apps
- `npm run lint` - Lint all packages
- `npm run type-check` - Type check all packages
- `npm run clean` - Clean all build artifacts
- `npm run format` - Format code with Prettier

## Packages

### @trellis/api

FastAPI-based backend that exposes the orchestrator endpoints.

Run locally without Docker:

```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

### @trellis/web

Next.js application with App Router, Tailwind CSS, and TypeScript.

### @trellis/ui

Shared UI components built with React and Tailwind CSS.

### @trellis/utils

Utility functions for common operations.

### @trellis/types

Shared TypeScript type definitions.

## Development

This monorepo uses:

- **Turbo** for build orchestration and caching
- **npm workspaces** for package management
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Prettier** for code formatting
- **ESLint** for code linting

## Docker Compose (optional reference)

The repository keeps a compose file for situations where you need a fully containerized stack (e.g., demos, CI, or a quick local Postgres instance). The same `.env` files are respected.

1. Ensure the environment files are populated (see steps above).
2. Start the stack:

   ```bash
   docker compose up
   ```

   The API listens on `http://localhost:4000` (FastAPI/Uvicorn) and the web app on `http://localhost:3000`.

3. Shut everything down when finished:

   ```bash
   docker compose down
   ```

## Adding New Packages

1. Create a new directory in `packages/`
2. Add a `package.json` with the `@trellis/` namespace
3. Update the root `package.json` workspaces if needed
4. Add TypeScript configuration
5. Export from the package's `src/index.ts`
