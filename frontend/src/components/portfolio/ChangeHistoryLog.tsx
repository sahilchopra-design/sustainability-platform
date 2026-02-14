import React, { useState } from 'react';
import { Undo2, Clock, User, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../ui/alert-dialog';
import { ChangeLog } from '../../types/portfolio';
import { cn } from '../../lib/utils';

export interface ChangeHistoryLogProps {
  changeLog: ChangeLog[];
  loading?: boolean;
  onUndo?: (changeId: string) => void;
}

export const ChangeHistoryLog: React.FC<ChangeHistoryLogProps> = ({
  changeLog,
  loading = false,
  onUndo,
}) => {
  const [undoing, setUndoing] = useState<string | null>(null);

  const getActionLabel = (action: string): string => {
    const labels: Record<string, string> = {
      create: 'Created',
      update: 'Updated',
      delete: 'Deleted',
      bulk_update: 'Bulk Updated',
      bulk_delete: 'Bulk Deleted',
    };
    return labels[action] || action;
  };

  const getActionColor = (action: string): string => {
    const colors: Record<string, string> = {
      create: 'text-[hsl(var(--success))]',
      update: 'text-[hsl(var(--info))]',
      delete: 'text-destructive',
      bulk_update: 'text-[hsl(var(--warning))]',
      bulk_delete: 'text-destructive',
    };
    return colors[action] || 'text-foreground';
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'null';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const handleUndo = async (changeId: string) => {
    if (!onUndo) return;
    setUndoing(changeId);
    await onUndo(changeId);
    setUndoing(null);
  };

  if (loading) {
    return (
      <Card data-testid="change-history-loading">
        <CardHeader>
          <CardTitle>Change History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading change history...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="change-history-log">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Change History
        </CardTitle>
        <CardDescription>
          View and revert recent changes to this portfolio
        </CardDescription>
      </CardHeader>
      <CardContent>
        {changeLog.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Clock className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p>No changes recorded yet</p>
          </div>
        ) : (
          <ScrollArea className="h-[500px] pr-4">
            <div className="space-y-4">
              {changeLog.map((change, index) => (
                <div key={change.id} data-testid={`change-log-item-${change.id}`}>
                  {index > 0 && <Separator className="my-4" />}
                  
                  <div className="space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn('text-xs', getActionColor(change.action))}
                            data-testid={`change-action-${change.id}`}
                          >
                            {getActionLabel(change.action)}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {change.entity_type}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span data-testid={`change-timestamp-${change.id}`}>
                            {formatTimestamp(change.timestamp)}
                          </span>
                          {change.user_id && (
                            <>
                              <span>•</span>
                              <User className="h-3 w-3" />
                              <span>User {change.user_id.slice(-8)}</span>
                            </>
                          )}
                        </div>
                      </div>
                      
                      {change.can_undo && onUndo && (
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={undoing === change.id}
                              data-testid={`undo-button-${change.id}`}
                            >
                              <Undo2 className="h-4 w-4 mr-2" />
                              Undo
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent data-testid={`undo-dialog-${change.id}`}>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Undo Change?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This will revert the {getActionLabel(change.action).toLowerCase()} operation.
                                {change.action === 'delete' && ' The deleted item will be restored.'}
                                {change.action === 'create' && ' The created item will be removed.'}
                                {change.action.includes('update') && ' Previous values will be restored.'}
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel data-testid={`undo-cancel-${change.id}`}>
                                Cancel
                              </AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleUndo(change.id)}
                                data-testid={`undo-confirm-${change.id}`}
                              >
                                Undo Change
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      )}
                    </div>

                    {/* Changes */}
                    {change.changes && change.changes.length > 0 && (
                      <div className="space-y-2">
                        {change.changes.map((fieldChange, idx) => (
                          <div
                            key={idx}
                            className="bg-muted/50 rounded-md p-3 text-sm"
                            data-testid={`change-field-${change.id}-${idx}`}
                          >
                            <div className="font-medium text-foreground mb-1">
                              {fieldChange.field}
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div>
                                <span className="text-muted-foreground">Before:</span>
                                <code className="block mt-1 bg-background px-2 py-1 rounded border border-border">
                                  {formatValue(fieldChange.old_value)}
                                </code>
                              </div>
                              <div>
                                <span className="text-muted-foreground">After:</span>
                                <code className="block mt-1 bg-background px-2 py-1 rounded border border-border">
                                  {formatValue(fieldChange.new_value)}
                                </code>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {!change.can_undo && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <AlertCircle className="h-3 w-3" />
                        <span>This change cannot be undone</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};