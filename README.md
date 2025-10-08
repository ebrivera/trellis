## Dev setup (npm only)

**Requirements**

- Node >= 18 (we use v22 fine)
- npm 9.8.1 (repo-managed via Corepack)

**Install & run**

```bash
# one-time
corepack enable || true
corepack prepare npm@9.8.1 --activate

# fresh install
rm -rf node_modules apps/web/node_modules
npm ci --include=dev

# dev
npm run dev          # runs all workspaces via turbo
# or just the web app:
npm run dev -w @trellis/web
```
