import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  MessageSquare,
  Clock,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Textarea } from '@/components/ui/Textarea';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/AlertDialog';
import { toast } from '@/components/ui/Toaster';
import type { Approval, ApprovalActionResult } from '@/types';
import { formatRelativeTime, cn } from '@/lib/utils';

const API_BASE = '/api';

export function ApprovalDetail() {
  const { approvalId } = useParams<{ approvalId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [approval, setApproval] = useState<Approval | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [discussOpen, setDiscussOpen] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [cancelOpen, setCancelOpen] = useState(false);

  // Check for action parameter from Teams button
  const actionParam = searchParams.get('action');

  useEffect(() => {
    if (approvalId) {
      fetchApproval();
    }
  }, [approvalId]);

  // Auto-trigger action if specified in URL
  useEffect(() => {
    if (approval && actionParam && approval.status === 'pending') {
      if (actionParam === 'approve') {
        // Show confirmation before auto-approving
        toast({
          title: 'Approval Required',
          description: `Click "Approve" to execute the plan for ${approval.task_name}`,
        });
      } else if (actionParam === 'discuss') {
        setDiscussOpen(true);
      } else if (actionParam === 'cancel') {
        setCancelOpen(true);
      }
    }
  }, [approval, actionParam]);

  const fetchApproval = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE}/approvals/${approvalId}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Approval not found');
        }
        throw new Error('Failed to fetch approval');
      }
      const data = await response.json();
      setApproval(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!approvalId) return;
    setActionLoading('approve');
    try {
      const response = await fetch(`${API_BASE}/approvals/${approvalId}/approve`, {
        method: 'POST',
      });
      const result: ApprovalActionResult = await response.json();
      if (result.success) {
        toast({ title: 'Plan approved!', description: 'Execution started.', variant: 'success' });
        if (result.approval) {
          setApproval(result.approval);
        }
        // Navigate to task detail to see execution
        if (approval?.task_id) {
          navigate(`/tasks/${approval.task_id}`);
        }
      } else {
        toast({ title: 'Approval failed', description: result.message, variant: 'destructive' });
      }
    } catch (e) {
      toast({
        title: 'Failed to approve',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDiscuss = async () => {
    if (!approvalId || !feedback.trim()) return;
    setActionLoading('discuss');
    try {
      const response = await fetch(`${API_BASE}/approvals/${approvalId}/discuss`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: feedback.trim() }),
      });
      const result: ApprovalActionResult = await response.json();
      if (result.success) {
        toast({ title: 'Feedback submitted', description: 'Plan is being revised.', variant: 'success' });
        if (result.approval) {
          setApproval(result.approval);
        }
        setFeedback('');
        setDiscussOpen(false);
      } else {
        toast({ title: 'Discussion failed', description: result.message, variant: 'destructive' });
      }
    } catch (e) {
      toast({
        title: 'Failed to submit feedback',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancel = async () => {
    if (!approvalId) return;
    setActionLoading('cancel');
    try {
      const response = await fetch(`${API_BASE}/approvals/${approvalId}/cancel`, {
        method: 'POST',
      });
      const result: ApprovalActionResult = await response.json();
      if (result.success) {
        toast({ title: 'Plan cancelled', variant: 'default' });
        if (result.approval) {
          setApproval(result.approval);
        }
        setCancelOpen(false);
      } else {
        toast({ title: 'Cancel failed', description: result.message, variant: 'destructive' });
      }
    } catch (e) {
      toast({
        title: 'Failed to cancel',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'success' | 'destructive' | 'warning' | 'secondary'> = {
      pending: 'warning',
      approved: 'success',
      executing: 'default',
      completed: 'success',
      cancelled: 'secondary',
      expired: 'secondary',
      failed: 'destructive',
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-lg font-medium">{error}</p>
        <Link to="/tasks">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Tasks
          </Button>
        </Link>
      </div>
    );
  }

  if (!approval) {
    return null;
  }

  const isPending = approval.status === 'pending';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link to={`/tasks/${approval.task_id}`}>
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-serif font-bold">Plan Approval</h1>
              {getStatusBadge(approval.status)}
            </div>
            <p className="text-muted-foreground">
              Task: <Link to={`/tasks/${approval.task_id}`} className="hover:underline">{approval.task_name}</Link>
            </p>
          </div>
        </div>

        {isPending && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setCancelOpen(true)}
              disabled={!!actionLoading}
            >
              <XCircle className="h-4 w-4 mr-1" />
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={() => setDiscussOpen(true)}
              disabled={!!actionLoading}
            >
              <MessageSquare className="h-4 w-4 mr-1" />
              Discuss
            </Button>
            <Button
              onClick={handleApprove}
              disabled={!!actionLoading}
              className="bg-green-600 hover:bg-green-700"
            >
              {actionLoading === 'approve' ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <CheckCircle className="h-4 w-4 mr-1" />
              )}
              Approve
            </Button>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Iteration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {approval.iteration + 1} / {approval.max_iterations}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg">{formatRelativeTime(approval.created_at)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Expires</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn("text-lg", isPending && "text-warning")}>
              <Clock className="h-4 w-4 inline mr-1" />
              {formatRelativeTime(approval.expires_at)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Plan Text */}
      <Card>
        <CardHeader>
          <CardTitle>Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap bg-muted p-4 rounded-lg text-sm overflow-auto max-h-[500px]">
            {approval.plan_text}
          </pre>
        </CardContent>
      </Card>

      {/* Feedback History */}
      {approval.feedback_history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Feedback History</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {approval.feedback_history.map((entry, i) => (
              <div key={i} className="border rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MessageSquare className="h-4 w-4" />
                  <span>{formatRelativeTime(entry.timestamp)}</span>
                </div>
                <p className="font-medium">{entry.feedback}</p>
                {entry.plan_response && (
                  <pre className="whitespace-pre-wrap bg-muted p-3 rounded text-sm">
                    {entry.plan_response}
                  </pre>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Final Output */}
      {approval.final_output && (
        <Card>
          <CardHeader>
            <CardTitle>Execution Output</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap bg-muted p-4 rounded-lg text-sm overflow-auto max-h-[400px]">
              {approval.final_output}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {approval.error && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-destructive">{approval.error}</p>
          </CardContent>
        </Card>
      )}

      {/* Discuss Dialog */}
      <AlertDialog open={discussOpen} onOpenChange={setDiscussOpen}>
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle>Provide Feedback</AlertDialogTitle>
            <AlertDialogDescription>
              Describe what changes you'd like to see in the plan. The AI will revise it based on your feedback.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Textarea
            placeholder="Enter your feedback..."
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={4}
          />
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDiscuss}
              disabled={!feedback.trim() || actionLoading === 'discuss'}
            >
              {actionLoading === 'discuss' ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <MessageSquare className="h-4 w-4 mr-1" />
              )}
              Submit Feedback
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Cancel Dialog */}
      <AlertDialog open={cancelOpen} onOpenChange={setCancelOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Plan</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel this plan? This will discard the planned changes.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep Plan</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancel}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={actionLoading === 'cancel'}
            >
              {actionLoading === 'cancel' ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <XCircle className="h-4 w-4 mr-1" />
              )}
              Cancel Plan
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
