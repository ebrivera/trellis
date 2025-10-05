import { Router } from 'express';
import { z } from 'zod';
import { asyncHandler, ApplicationError, withErrorHandling } from '../lib/errors';
import { withAuditLog } from '../lib/audit';
import type { OperationContext } from '../lib/types';

const router = Router();

router.get(
  '/health',
  asyncHandler(async (_req, res) => {
    res.json({
      status: 'ok',
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    });
  })
);

const orchestrateRequestSchema = z
  .object({
    request: z.string().optional(),
    template: z.enum(['matching', 'monitoring', 'analysis']).optional(),
    params: z.record(z.string(), z.unknown()).optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  })
  .strict();

type OrchestrateRequest = z.infer<typeof orchestrateRequestSchema>;

type OrchestrateResponse = {
  status: 'pending';
  workflow: {
    template: 'matching' | 'monitoring' | 'analysis';
    params: Record<string, unknown>;
  };
  message: string;
  receivedAt: string;
};

const orchestrateWorkflow = withErrorHandling<OrchestrateRequest, OrchestrateResponse>(
  withAuditLog<OrchestrateRequest, OrchestrateResponse>(
    'orchestrate_workflow',
    async (payload: OrchestrateRequest, context?: OperationContext) => {
      const template = payload.template ?? 'matching';
      const params = payload.params ?? {};

      return {
        status: 'pending',
        workflow: {
          template,
          params,
        },
        message: 'Workflow queued for approval. Implement executor to continue.',
        receivedAt: new Date().toISOString(),
      } satisfies OrchestrateResponse;
    }
  ),
  {
    operation: 'orchestrate_workflow',
    defaultMessage: 'Failed to orchestrate workflow request',
  }
);

router.post(
  '/orchestrate',
  asyncHandler(async (req, res) => {
    const parsed = orchestrateRequestSchema.parse(req.body ?? {});

    const context: OperationContext = {
      userId: req.header('x-user-id') ?? undefined,
      requestId: req.header('x-request-id') ?? undefined,
      source: 'api',
      metadata: parsed.metadata ?? undefined,
    };

    const result = await orchestrateWorkflow(parsed, context);
    res.status(202).json(result);
  })
);

const approvalParamsSchema = z.object({
  id: z.string().min(1),
});

type ApprovalLookupParams = z.infer<typeof approvalParamsSchema>;

type ApprovalResponse = {
  id: string;
  status: 'pending' | 'approved' | 'rejected';
  changes: Array<Record<string, unknown>>;
  nextActions: Array<{ label: string; href: string }>;
};

const fetchApproval = withErrorHandling<ApprovalLookupParams, ApprovalResponse>(
  withAuditLog<ApprovalLookupParams, ApprovalResponse>(
    'fetch_approval_gate',
    async ({ id }) => {
      if (!id) {
        throw new ApplicationError('Approval identifier is required', {
          status: 400,
          code: 'MISSING_ID',
        });
      }

      return {
        id,
        status: 'pending',
        changes: [],
        nextActions: [
          { label: 'Approve', href: `/approval/${id}/approve` },
          { label: 'Reject', href: `/approval/${id}/reject` },
        ],
      } satisfies ApprovalResponse;
    }
  ),
  {
    operation: 'fetch_approval_gate',
    defaultMessage: 'Unable to load approval gate',
  }
);

router.get(
  '/approval/:id',
  asyncHandler(async (req, res) => {
    const params = approvalParamsSchema.parse(req.params);
    const context: OperationContext = {
      requestId: req.header('x-request-id') ?? undefined,
      source: 'api',
    };
    const result = await fetchApproval(params, context);
    res.json(result);
  })
);

export default router;
