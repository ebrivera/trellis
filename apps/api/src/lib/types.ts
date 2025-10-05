export interface OperationContext {
  userId?: string;
  requestId?: string;
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface OperationResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}
