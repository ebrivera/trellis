# Trellis

A modern monorepo with Next.js, Tailwind CSS, and TypeScript.

## Structure

```
trellis/
├── apps/
│   ├── api/                 # Express API skeleton
│   └── web/                 # Next.js application
├── packages/
│   ├── ui/                  # Shared UI components
│   ├── utils/               # Utility functions
│   └── types/               # Shared TypeScript types
├── package.json             # Root package.json with workspaces
├── turbo.json              # Turbo configuration
└── tsconfig.json           # Root TypeScript configuration
```

## Getting Started

1. Install dependencies:

   ```bash
   npm install
   ```

2. Start development servers:

   ```bash
   npm run dev
   ```

3. Build all packages:
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

Express-based API service that exposes the orchestrator endpoints.

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

## Docker Compose

1. Copy the example environment files and adjust as needed:

   ```bash
   cp apps/api/.env.example apps/api/.env
   cp apps/web/.env.example apps/web/.env.local
   ```

2. Start the full stack (Postgres, API, and Next.js):

   ```bash
   docker compose up
   ```

   The API listens on `http://localhost:4000` and the web app on `http://localhost:3000`.

3. Stop and remove containers:

   ```bash
   docker compose down
   ```

## Adding New Packages

1. Create a new directory in `packages/`
2. Add a `package.json` with the `@trellis/` namespace
3. Update the root `package.json` workspaces if needed
4. Add TypeScript configuration
5. Export from the package's `src/index.ts`
