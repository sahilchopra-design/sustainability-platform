import React, { useState, useMemo } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { ValidationError } from '../../types/upload';
import { cn } from '../../lib/utils';

export interface ValidationSummary {
  total: number;
  valid: number;
  warnings: number;
  errors: number;
}

export interface ValidationResultsPanelProps {
  summary: ValidationSummary;
  errors: ValidationError[];
  onFixError?: (error: ValidationError, newValue: string) => void;
}

export const ValidationResultsPanel: React.FC<ValidationResultsPanelProps> = ({
  summary,
  errors,
  onFixError,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'errors' | 'warnings' | 'info'>('all');
  const [editingError, setEditingError] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const filteredErrors = useMemo(() => {
    if (activeTab === 'all') return errors;
    return errors.filter((e) => e.severity === activeTab.slice(0, -1)); // 'errors' -> 'error'
  }, [errors, activeTab]);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="h-4 w-4 text-destructive" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-[hsl(var(--warning))]" />;
      case 'info':
        return <Info className="h-4 w-4 text-[hsl(var(--info))]" />;
      default:
        return null;
    }
  };

  const getSeverityBadgeVariant = (severity: string): 'destructive' | 'secondary' | 'outline' => {
    switch (severity) {
      case 'error':
        return 'destructive';
      case 'warning':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const handleStartEdit = (error: ValidationError) => {
    const errorKey = `${error.row_number}-${error.column_name}`;
    setEditingError(errorKey);
    setEditValue(error.original_value || '');
  };

  const handleSaveEdit = (error: ValidationError) => {
    if (onFixError) {
      onFixError(error, editValue);
    }
    setEditingError(null);
    setEditValue('');
  };

  const handleCancelEdit = () => {
    setEditingError(null);
    setEditValue('');
  };

  const getSuccessRate = () => {
    if (summary.total === 0) return 0;
    return Math.round((summary.valid / summary.total) * 100);
  };

  return (
    <div className="space-y-4" data-testid="validation-results-panel">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card data-testid="validation-summary-total">
          <CardHeader className="pb-3">
            <CardDescription>Total Rows</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold tabular-nums">{summary.total}</div>
          </CardContent>
        </Card>

        <Card data-testid="validation-summary-valid">
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-[hsl(var(--success))]" />
              Valid
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <div className="text-2xl font-semibold tabular-nums text-[hsl(var(--success))]">
                {summary.valid}
              </div>
              <div className="text-sm text-muted-foreground">{getSuccessRate()}%</div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="validation-summary-warnings">
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 text-[hsl(var(--warning))]" />
              Warnings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold tabular-nums text-[hsl(var(--warning))]">
              {summary.warnings}
            </div>
          </CardContent>
        </Card>

        <Card data-testid="validation-summary-errors">
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-1">
              <XCircle className="h-3 w-3 text-destructive" />
              Errors
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold tabular-nums text-destructive">
              {summary.errors}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Issues Table */}
      <Card>
        <CardHeader>
          <CardTitle>Validation Issues</CardTitle>
          <CardDescription>
            Review and fix validation errors before importing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
            <TabsList className="mb-4" data-testid="validation-filter-tabs">
              <TabsTrigger value="all" data-testid="validation-tab-all">
                All ({errors.length})
              </TabsTrigger>
              <TabsTrigger value="errors" data-testid="validation-tab-errors">
                Errors ({summary.errors})
              </TabsTrigger>
              <TabsTrigger value="warnings" data-testid="validation-tab-warnings">
                Warnings ({summary.warnings})
              </TabsTrigger>
              <TabsTrigger value="info" data-testid="validation-tab-info">
                Info
              </TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab} className="mt-0">
              {filteredErrors.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-4 text-[hsl(var(--success))]" />
                  <p>No {activeTab === 'all' ? 'issues' : activeTab} found</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table data-testid="validation-issues-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-20">Row</TableHead>
                        <TableHead className="w-32">Column</TableHead>
                        <TableHead className="w-24">Type</TableHead>
                        <TableHead>Issue</TableHead>
                        <TableHead className="w-32">Value</TableHead>
                        {onFixError && <TableHead className="w-24">Action</TableHead>}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredErrors.map((error, index) => {
                        const errorKey = `${error.row_number}-${error.column_name}`;
                        const isEditing = editingError === errorKey;

                        return (
                          <TableRow
                            key={index}
                            data-testid={`validation-error-row-${index}`}
                          >
                            <TableCell className="font-mono text-xs tabular-nums">
                              {error.row_number || '-'}
                            </TableCell>
                            <TableCell className="font-mono text-xs">
                              {error.column_name || '-'}
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={getSeverityBadgeVariant(error.severity)}
                                className="text-xs"
                              >
                                <span className="mr-1">{getSeverityIcon(error.severity)}</span>
                                {error.severity}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-sm">{error.error_message}</TableCell>
                            <TableCell>
                              {isEditing ? (
                                <Input
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  className="h-8 text-xs"
                                  data-testid={`edit-error-input-${index}`}
                                />
                              ) : (
                                <code className="text-xs bg-muted px-2 py-1 rounded">
                                  {error.original_value || 'null'}
                                </code>
                              )}
                            </TableCell>
                            {onFixError && (
                              <TableCell>
                                {isEditing ? (
                                  <div className="flex gap-1">
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => handleSaveEdit(error)}
                                      className="h-7 px-2 text-xs"
                                      data-testid={`save-error-fix-${index}`}
                                    >
                                      Save
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={handleCancelEdit}
                                      className="h-7 px-2 text-xs"
                                      data-testid={`cancel-error-fix-${index}`}
                                    >
                                      Cancel
                                    </Button>
                                  </div>
                                ) : (
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleStartEdit(error)}
                                    disabled={error.severity !== 'error'}
                                    className="h-7 px-2 text-xs"
                                    data-testid={`fix-error-${index}`}
                                  >
                                    Fix
                                  </Button>
                                )}
                              </TableCell>
                            )}
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};