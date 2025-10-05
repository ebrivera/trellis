import type { NextFunction, Request, Response } from 'express';
import type { OperationContext } from './types';

type AnyError = Error & { status?: number; code?: string; details?: unknown };

type ErrorLogger = (
  error: AnyError,
  context: {
    params: unknown;
    operation?: string;
    operationContext?: OperationContext;
  }
) => void;

export class ApplicationError extends Error {
  public status: number;
  public code: string;
  public details?: unknown;

  constructor(message: string, options?: { status?: number; code?: string; details?: unknown; cause?: unknown }) {
    super(message);
    this.name = 'ApplicationError';
    this.status = options?.status ?? 500;
    this.code = options?.code ?? 'INTERNAL_ERROR';
    this.details = options?.details;

    if (options?.cause) {
      // Preserve the original error when available.
      (this as Error & { cause?: unknown }).cause = options.cause;
    }
  }
}

const defaultErrorLogger: ErrorLogger = (error, context) => {
  console.error('[error-handler]', {
    message: error.message,
    stack: error.stack,
    code: error.code,
    status: error.status,
    params: context.params,
    operation: context.operation,
    operationContext: context.operationContext,
  });
};

export function withErrorHandling<TParams, TResult>(
  fn: (params: TParams, context?: OperationContext) => Promise<TResult> | TResult,
  options?: { operation?: string; logger?: ErrorLogger; defaultMessage?: string }
) {
  return async (params: TParams, context?: OperationContext): Promise<TResult> => {
    const logger = options?.logger ?? defaultErrorLogger;
    const operation = options?.operation;

    try {
      return await fn(params, context);
    } catch (error) {
      const err = error as AnyError;
      logger(err, { params, operation, operationContext: context });

      if (err instanceof ApplicationError) {
        throw err;
      }

      throw new ApplicationError(options?.defaultMessage ?? 'Unexpected error', {
        cause: err,
      });
    }
  };
}

export function asyncHandler<Params = unknown>(
  handler: (req: Request, res: Response, next: NextFunction) => Promise<Params> | Params
) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(handler(req, res, next)).catch(next);
  };
}

export function notFoundHandler(req: Request, res: Response) {
  res.status(404).json({
    error: 'NotFound',
    message: `Route ${req.method} ${req.path} does not exist`,
  });
}

export function errorHandler(error: unknown, req: Request, res: Response, _next: NextFunction) {
  const err = error as AnyError;
  const status = err.status ?? 500;
  const code = err.code ?? 'INTERNAL_ERROR';

  if (status >= 500) {
    console.error('[express-error]', {
      method: req.method,
      path: req.path,
      message: err.message,
      stack: err.stack,
      code,
    });
  }

  res.status(status).json({
    error: code,
    message: err.message ?? 'Unexpected error',
    details: err.details,
  });
}
