import cors from 'cors';
import express from 'express';
import morgan from 'morgan';
import routes from './routes';
import { errorHandler, notFoundHandler } from './lib/errors';

export function createApp() {
  const app = express();

  app.use(cors());
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true }));
  app.use(morgan('dev'));

  app.use(routes);

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}
