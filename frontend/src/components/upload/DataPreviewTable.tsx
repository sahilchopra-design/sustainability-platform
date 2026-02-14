import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, CheckCircle2, AlertTriangle, XCircle, Edit2, Check, X } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Checkbox } from '../ui/checkbox';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { cn } from '../../lib/utils';

export type ValidationStatus = 'valid' | 'warning' | 'error';

export interface DataRow {
  _rowId: number;
  _status: ValidationStatus;
  [key: string]: any;
}

export interface DataPreviewTableProps {
  data: DataRow[];
  columns: string[];
  totalRows: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onCellEdit?: (rowId: number, column: string, newValue: any) => void;
  onRowSelect?: (rowIds: number[]) => void;
  selectedRows?: number[];
}

export const DataPreviewTable: React.FC<DataPreviewTableProps> = ({
  data,
  columns,
  totalRows,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onCellEdit,
  onRowSelect,
  selectedRows = [],
}) => {
  const [editingCell, setEditingCell] = useState<{ rowId: number; column: string } | null>(null);
  const [editValue, setEditValue] = useState('');

  const totalPages = Math.ceil(totalRows / pageSize);
  const startRow = (page - 1) * pageSize + 1;
  const endRow = Math.min(page * pageSize, totalRows);

  const allRowsSelected = useMemo(() => {
    if (data.length === 0) return false;
    return data.every((row) => selectedRows.includes(row._rowId));
  }, [data, selectedRows]);

  const someRowsSelected = useMemo(() => {
    return selectedRows.length > 0 && !allRowsSelected;
  }, [selectedRows, allRowsSelected]);

  const handleSelectAll = () => {
    if (onRowSelect) {
      if (allRowsSelected) {
        onRowSelect([]);
      } else {
        onRowSelect(data.map((row) => row._rowId));
      }
    }
  };

  const handleSelectRow = (rowId: number) => {
    if (onRowSelect) {
      if (selectedRows.includes(rowId)) {
        onRowSelect(selectedRows.filter((id) => id !== rowId));
      } else {
        onRowSelect([...selectedRows, rowId]);
      }
    }
  };

  const handleStartEdit = (rowId: number, column: string, currentValue: any) => {
    setEditingCell({ rowId, column });
    setEditValue(String(currentValue || ''));
  };

  const handleSaveEdit = () => {
    if (editingCell && onCellEdit) {
      onCellEdit(editingCell.rowId, editingCell.column, editValue);
    }
    setEditingCell(null);
    setEditValue('');
  };

  const handleCancelEdit = () => {
    setEditingCell(null);
    setEditValue('');
  };

  const getStatusIcon = (status: ValidationStatus) => {
    switch (status) {
      case 'valid':
        return <CheckCircle2 className="h-4 w-4 text-[hsl(var(--success))]" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-[hsl(var(--warning))]" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-destructive" />;
    }
  };

  const getStatusColor = (status: ValidationStatus): string => {
    switch (status) {
      case 'valid':
        return 'bg-[hsl(var(--success))]/10';
      case 'warning':
        return 'bg-[hsl(var(--warning))]/10';
      case 'error':
        return 'bg-destructive/10';
    }
  };

  return (
    <Card data-testid="data-preview-table">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Data Preview</CardTitle>
            <CardDescription className="mt-1">
              Showing {startRow} - {endRow} of {totalRows} rows
            </CardDescription>
          </div>
          {selectedRows.length > 0 && (
            <Badge variant="secondary" data-testid="selected-rows-badge">
              {selectedRows.length} row{selectedRows.length !== 1 ? 's' : ''} selected
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  {onRowSelect && (
                    <TableHead className="w-12 sticky left-0 bg-card z-10">
                      <Checkbox
                        checked={allRowsSelected}
                        indeterminate={someRowsSelected}
                        onCheckedChange={handleSelectAll}
                        data-testid="select-all-checkbox"
                      />
                    </TableHead>
                  )}
                  <TableHead className="w-16 sticky left-0 bg-card z-10">Status</TableHead>
                  <TableHead className="w-20 sticky left-12 bg-card z-10 font-mono">Row</TableHead>
                  {columns.map((col) => (
                    <TableHead key={col} className="min-w-[150px]">
                      {col}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length + (onRowSelect ? 3 : 2)}
                      className="text-center py-12 text-muted-foreground"
                    >
                      No data to display
                    </TableCell>
                  </TableRow>
                ) : (
                  data.map((row) => {
                    const isSelected = selectedRows.includes(row._rowId);

                    return (
                      <TableRow
                        key={row._rowId}
                        className={cn(
                          isSelected && 'bg-accent/50',
                          getStatusColor(row._status)
                        )}
                        data-testid={`preview-row-${row._rowId}`}
                      >
                        {onRowSelect && (
                          <TableCell className="sticky left-0 bg-inherit z-10">
                            <Checkbox
                              checked={isSelected}
                              onCheckedChange={() => handleSelectRow(row._rowId)}
                              data-testid={`select-row-${row._rowId}`}
                            />
                          </TableCell>
                        )}
                        <TableCell className="sticky left-0 bg-inherit z-10">
                          {getStatusIcon(row._status)}
                        </TableCell>
                        <TableCell className="sticky left-12 bg-inherit z-10 font-mono text-xs tabular-nums">
                          {row._rowId}
                        </TableCell>
                        {columns.map((col) => {
                          const isEditing =
                            editingCell?.rowId === row._rowId && editingCell?.column === col;

                          return (
                            <TableCell
                              key={col}
                              className="text-sm"
                              data-testid={`cell-${row._rowId}-${col}`}
                            >
                              {isEditing ? (
                                <div className="flex items-center gap-1">
                                  <Input
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    className="h-8 text-xs"
                                    autoFocus
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter') handleSaveEdit();
                                      if (e.key === 'Escape') handleCancelEdit();
                                    }}
                                    data-testid={`edit-cell-input-${row._rowId}-${col}`}
                                  />
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-7 w-7 p-0"
                                    onClick={handleSaveEdit}
                                    data-testid={`save-cell-${row._rowId}-${col}`}
                                  >
                                    <Check className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-7 w-7 p-0"
                                    onClick={handleCancelEdit}
                                    data-testid={`cancel-cell-${row._rowId}-${col}`}
                                  >
                                    <X className="h-4 w-4" />
                                  </Button>
                                </div>
                              ) : (
                                <div className="group flex items-center justify-between gap-2">
                                  <span className="truncate">{row[col] ?? '-'}</span>
                                  {onCellEdit && row._status === 'error' && (
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                      onClick={() => handleStartEdit(row._rowId, col, row[col])}
                                      data-testid={`edit-cell-${row._rowId}-${col}`}
                                    >
                                      <Edit2 className="h-3 w-3" />
                                    </Button>
                                  )}
                                </div>
                              )}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Rows per page:</span>
            <Select
              value={String(pageSize)}
              onValueChange={(value) => onPageSizeChange(Number(value))}
            >
              <SelectTrigger className="w-20 h-8" data-testid="page-size-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page === 1}
              data-testid="prev-page-button"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-muted-foreground tabular-nums" data-testid="page-info">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page === totalPages}
              data-testid="next-page-button"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};