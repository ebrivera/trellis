import { randomUUID } from 'crypto';
import type { OperationContext } from './types';

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  functionName: string;
  params: unknown;
  result?: unknown;
  success: boolean;
  userId?: string;
  requestId?: string;
  source?: string;
  errorMessage?: string;
  metadata?: Record<string, unknown>;
}

export type AuditLogger = (entry: AuditLogEntry) => Promise<void> | void;

const defaultLogger: AuditLogger = async (entry) => {
  const { id, timestamp, functionName, success } = entry;
  // TODO: Replace console log with persistent storage write (audit_log table).
  console.info('[audit]', { id, timestamp, functionName, success, entry });
};

const safeSerialize = (value: unknown) => {
  try {
    return JSON.parse(JSON.stringify(value));
  } catch (error) {
    return '[unserializable]';
  }
};

export async function logAuditEntry(entry: AuditLogEntry, logger: AuditLogger = defaultLogger) {
  await logger({
    ...entry,
    params: safeSerialize(entry.params),
    result: safeSerialize(entry.result),
    metadata: entry.metadata ? safeSerialize(entry.metadata) : undefined,
  });
}

export function withAuditLog<TParams, TResult>(
  functionName: string,
  fn: (params: TParams, context?: OperationContext) => Promise<TResult> | TResult,
  logger: AuditLogger = defaultLogger
) {
  return async (params: TParams, context?: OperationContext): Promise<TResult> => {
    const auditBase: Omit<AuditLogEntry, 'params' | 'result' | 'errorMessage' | 'success'> = {
      id: randomUUID(),
      timestamp: new Date().toISOString(),
      functionName,
      userId: context?.userId,
      requestId: context?.requestId,
      source: context?.source,
      metadata: context?.metadata,
    };

    try {
      const result = await fn(params, context);
      await logAuditEntry({
        ...auditBase,
        params,
        result,
        success: true,
      }, logger);
      return result;
    } catch (error) {
      await logAuditEntry({
        ...auditBase,
        params,
        success: false,
        errorMessage: error instanceof Error ? error.message : String(error),
      }, logger);
      throw error;
    }
  };
}
