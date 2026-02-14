import React from 'react';
import { Download, Trash2, Edit2, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { Separator } from '../ui/separator';

export interface BulkEditToolbarProps {
  selectedCount: number;
  onBulkUpdate?: () => void;
  onBulkDelete?: () => void;
  onExport?: () => void;
  onClearSelection: () => void;
  disabled?: boolean;
}

export const BulkEditToolbar: React.FC<BulkEditToolbarProps> = ({
  selectedCount,
  onBulkUpdate,
  onBulkDelete,
  onExport,
  onClearSelection,
  disabled = false,
}) => {
  if (selectedCount === 0) {
    return null;
  }

  return (
    <div
      className="flex items-center justify-between gap-4 px-4 py-3 bg-accent/50 border border-border rounded-lg"
      data-testid="bulk-edit-toolbar"
    >
      <div className="flex items-center gap-3">
        <Badge variant="secondary" className="tabular-nums" data-testid="selected-count-badge">
          {selectedCount} selected
        </Badge>
        <Separator orientation="vertical" className="h-6" />
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearSelection}
          disabled={disabled}
          data-testid="clear-selection-button"
        >
          <X className="h-4 w-4 mr-2" />
          Clear
        </Button>
      </div>

      <div className="flex items-center gap-2">
        {onBulkUpdate && (
          <Button
            variant="outline"
            size="sm"
            onClick={onBulkUpdate}
            disabled={disabled}
            data-testid="bulk-update-button"
          >
            <Edit2 className="h-4 w-4 mr-2" />
            Update
          </Button>
        )}
        
        {onExport && (
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            disabled={disabled}
            data-testid="bulk-export-button"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        )}
        
        {onBulkDelete && (
          <Button
            variant="outline"
            size="sm"
            onClick={onBulkDelete}
            disabled={disabled}
            className="text-destructive hover:text-destructive"
            data-testid="bulk-delete-button"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        )}
      </div>
    </div>
  );
};