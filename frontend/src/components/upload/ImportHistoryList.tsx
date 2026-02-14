import React from 'react';
import { Clock, CheckCircle2, XCircle, AlertCircle, MoreVertical, Eye, RotateCcw, Trash2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { UploadStatus } from '../../types/upload';
import { cn } from '../../lib/utils';

export interface ImportHistoryListProps {
  uploads: UploadStatus[];
  onView?: (uploadId: string) => void;
  onRetry?: (uploadId: string) => void;
  onDelete?: (uploadId: string) => void;
}

export const ImportHistoryList: React.FC<ImportHistoryListProps> = ({
  uploads,
  onView,
  onRetry,
  onDelete,
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-[hsl(var(--success))]" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-destructive" />;
      case 'uploaded':
      case 'validating':
      case 'mapping':
      case 'processing':
        return <Clock className="h-4 w-4 text-[hsl(var(--info))]" />;
      default:
        return <AlertCircle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadgeVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'failed':
        return 'destructive';
      case 'uploaded':
      case 'validating':
      case 'mapping':
      case 'processing':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getStatusLabel = (status: string): string => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
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

  return (
    <Card data-testid="import-history-list">
      <CardHeader>
        <CardTitle>Import History</CardTitle>
        <CardDescription>Recent portfolio file uploads and imports</CardDescription>
      </CardHeader>
      <CardContent>
        {uploads.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Clock className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p>No import history yet</p>
            <p className="text-xs mt-1">Upload a file to get started</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-3">
              {uploads.map((upload, index) => (
                <div key={upload.upload_id} data-testid={`history-item-${upload.upload_id}`}>
                  {index > 0 && <Separator className="mb-3" />}
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-muted">
                      {getStatusIcon(upload.status)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate" data-testid={`history-upload-id-${upload.upload_id}`}>
                            Upload #{upload.upload_id.slice(-8)}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {formatDate(upload.created_at)}
                          </p>
                        </div>
                        <Badge
                          variant={getStatusBadgeVariant(upload.status)}
                          className="text-xs"
                          data-testid={`history-status-${upload.upload_id}`}
                        >
                          {getStatusLabel(upload.status)}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="tabular-nums">
                          Total: <span className="font-medium text-foreground">{upload.total_rows}</span>
                        </span>
                        {upload.status === 'completed' && (
                          <>
                            <span className="tabular-nums">
                              Valid: <span className="font-medium text-[hsl(var(--success))]">{upload.valid_rows}</span>
                            </span>
                            {upload.invalid_rows > 0 && (
                              <span className="tabular-nums">
                                Invalid: <span className="font-medium text-destructive">{upload.invalid_rows}</span>
                              </span>
                            )}
                          </>
                        )}
                        {upload.status === 'processing' && upload.processed_rows !== undefined && (
                          <span className="tabular-nums">
                            Processed: <span className="font-medium text-foreground">
                              {upload.processed_rows}/{upload.total_rows}
                            </span>
                          </span>
                        )}
                      </div>

                      {upload.error_message && (
                        <div className="mt-2 text-xs text-destructive bg-destructive/10 px-2 py-1 rounded">
                          {upload.error_message}
                        </div>
                      )}
                    </div>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                          data-testid={`history-actions-${upload.upload_id}`}
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {onView && (
                          <DropdownMenuItem
                            onClick={() => onView(upload.upload_id)}
                            data-testid={`view-upload-${upload.upload_id}`}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                        )}
                        {onRetry && upload.status === 'failed' && (
                          <DropdownMenuItem
                            onClick={() => onRetry(upload.upload_id)}
                            data-testid={`retry-upload-${upload.upload_id}`}
                          >
                            <RotateCcw className="h-4 w-4 mr-2" />
                            Retry Import
                          </DropdownMenuItem>
                        )}
                        {onDelete && (
                          <DropdownMenuItem
                            onClick={() => onDelete(upload.upload_id)}
                            className="text-destructive focus:text-destructive"
                            data-testid={`delete-upload-${upload.upload_id}`}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
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