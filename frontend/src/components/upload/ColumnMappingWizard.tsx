import React, { useState, useEffect } from 'react';
import { ArrowRight, Save, Wand2, RotateCcw, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Alert, AlertDescription } from '../ui/alert';
import { Separator } from '../ui/separator';
import { ScrollArea } from '../ui/scroll-area';
import { cn } from '../../lib/utils';
import { ColumnMapping, MappingSuggestion } from '../../hooks/useColumnMapping';

export interface RequiredField {
  key: string;
  label: string;
  required: boolean;
}

export interface ColumnMappingWizardProps {
  fileColumns: string[];
  requiredFields: RequiredField[];
  mapping: ColumnMapping;
  suggestions: MappingSuggestion[];
  onMappingChange: (systemField: string, fileColumn: string | null) => void;
  onAutoMap: () => void;
  onClear: () => void;
  onComplete: () => void;
  onSaveTemplate?: (name: string, description?: string) => Promise<void>;
}

export const ColumnMappingWizard: React.FC<ColumnMappingWizardProps> = ({
  fileColumns,
  requiredFields,
  mapping,
  suggestions,
  onMappingChange,
  onAutoMap,
  onClear,
  onComplete,
  onSaveTemplate,
}) => {
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  const getSuggestion = (systemField: string): MappingSuggestion | undefined => {
    return suggestions.find((s) => s.systemField === systemField);
  };

  const getConfidenceBadgeVariant = (confidence: number): 'default' | 'secondary' | 'outline' => {
    if (confidence >= 80) return 'default';
    if (confidence >= 60) return 'secondary';
    return 'outline';
  };

  const getMappingCompleteness = (): { total: number; mapped: number; requiredMapped: number; requiredTotal: number } => {
    const total = requiredFields.length;
    const mapped = Object.keys(mapping).length;
    const requiredTotal = requiredFields.filter((f) => f.required).length;
    const requiredMapped = requiredFields.filter((f) => f.required && mapping[f.key]).length;
    return { total, mapped, requiredMapped, requiredTotal };
  };

  const completeness = getMappingCompleteness();
  const isComplete = completeness.requiredMapped === completeness.requiredTotal;

  const handleSaveTemplate = async () => {
    if (!onSaveTemplate) return;
    await onSaveTemplate(templateName, templateDescription);
    setShowSaveDialog(false);
    setTemplateName('');
    setTemplateDescription('');
  };

  return (
    <Card data-testid="column-mapping-wizard">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Map Columns</CardTitle>
            <CardDescription className="mt-1">
              Map your file columns to required portfolio holdings fields
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onAutoMap}
              data-testid="auto-map-button"
            >
              <Wand2 className="h-4 w-4 mr-2" />
              Auto-Map
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClear}
              data-testid="clear-mapping-button"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>

        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-muted-foreground">Mapping Progress</span>
            <span className="font-medium tabular-nums" data-testid="mapping-progress-text">
              {completeness.mapped} / {completeness.total} fields
              {completeness.requiredTotal > 0 && (
                <span className="text-muted-foreground ml-1">
                  ({completeness.requiredMapped}/{completeness.requiredTotal} required)
                </span>
              )}
            </span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full transition-all duration-300',
                isComplete ? 'bg-[hsl(var(--success))]' : 'bg-primary'
              )}
              style={{ width: `${(completeness.mapped / completeness.total) * 100}%` }}
              data-testid="mapping-progress-bar"
            />
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-4">
            {requiredFields.map((field) => {
              const suggestion = getSuggestion(field.key);
              const currentMapping = mapping[field.key];
              const isMapped = !!currentMapping;

              return (
                <div
                  key={field.key}
                  className="space-y-2 p-4 border border-border rounded-lg"
                  data-testid={`mapping-field-${field.key}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <Label className="text-sm font-medium">
                        {field.label}
                        {field.required && (
                          <span className="text-destructive ml-1" aria-label="required">
                            *
                          </span>
                        )}
                      </Label>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        System field: <code className="font-mono">{field.key}</code>
                      </p>
                    </div>
                    {isMapped && (
                      <CheckCircle2 className="h-5 w-5 text-[hsl(var(--success))] flex-shrink-0" />
                    )}
                  </div>

                  <Select
                    value={currentMapping || ''}
                    onValueChange={(value) => onMappingChange(field.key, value || null)}
                  >
                    <SelectTrigger
                      className="w-full"
                      data-testid={`mapping-select-${field.key}`}
                    >
                      <SelectValue placeholder="Select column..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">None</SelectItem>
                      {fileColumns.map((col) => (
                        <SelectItem key={col} value={col}>
                          {col}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {suggestion && !currentMapping && (
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-muted-foreground">Suggested:</span>
                      <Badge
                        variant={getConfidenceBadgeVariant(suggestion.confidence)}
                        className="text-xs"
                      >
                        {suggestion.suggestedColumn}
                      </Badge>
                      <Badge variant="outline" className="text-xs tabular-nums">
                        {suggestion.confidence}% match
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 ml-auto"
                        onClick={() => onMappingChange(field.key, suggestion.suggestedColumn)}
                        data-testid={`apply-suggestion-${field.key}`}
                      >
                        Apply
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>

        <Separator className="my-6" />

        <div className="flex items-center justify-between gap-4">
          <div className="flex gap-2">
            {onSaveTemplate && (
              <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
                <DialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!isComplete}
                    data-testid="save-template-button"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save as Template
                  </Button>
                </DialogTrigger>
                <DialogContent data-testid="save-template-dialog">
                  <DialogHeader>
                    <DialogTitle>Save Mapping Template</DialogTitle>
                    <DialogDescription>
                      Save this column mapping configuration for future uploads
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="template-name">Template Name</Label>
                      <Input
                        id="template-name"
                        placeholder="e.g., Standard Portfolio Format"
                        value={templateName}
                        onChange={(e) => setTemplateName(e.target.value)}
                        data-testid="template-name-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="template-description">Description (optional)</Label>
                      <Input
                        id="template-description"
                        placeholder="Brief description of this mapping"
                        value={templateDescription}
                        onChange={(e) => setTemplateDescription(e.target.value)}
                        data-testid="template-description-input"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => setShowSaveDialog(false)}
                      data-testid="cancel-save-template-button"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleSaveTemplate}
                      disabled={!templateName.trim()}
                      data-testid="confirm-save-template-button"
                    >
                      Save Template
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </div>

          <Button
            onClick={onComplete}
            disabled={!isComplete}
            size="default"
            data-testid="complete-mapping-button"
          >
            Continue to Validation
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>

        {!isComplete && (
          <Alert className="mt-4" data-testid="mapping-incomplete-alert">
            <AlertDescription>
              Please map all required fields ({completeness.requiredMapped}/{completeness.requiredTotal} completed)
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};