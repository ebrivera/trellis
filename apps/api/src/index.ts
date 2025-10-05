import http from 'http';
import { createApp } from './app';
import { config } from './config';

const app = createApp();
const server = http.createServer(app);

server.listen(config.port, () => {
  console.log(`API server listening on http://localhost:${config.port}`);
});

const shutdown = (signal: NodeJS.Signals) => {
  console.log(`Received ${signal}. Shutting down gracefully.`);
  server.close(() => {
    process.exit(0);
  });
};

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
