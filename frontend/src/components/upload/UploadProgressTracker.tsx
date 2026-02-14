import React from 'react';
import { CheckCircle2, Circle, Loader2, XCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Separator } from '../ui/separator';
import { cn } from '../../lib/utils';

export type UploadStep =
  | 'uploaded'
  | 'validating'
  | 'mapping'
  | 'processing'
  | 'completed'
  | 'failed';

export interface StepInfo {
  id: UploadStep;
  label: string;
  description: string;
}

const STEPS: StepInfo[] = [
  { id: 'uploaded', label: 'Uploaded', description: 'File uploaded successfully' },
  { id: 'validating', label: 'Validating', description: 'Checking data quality and format' },
  { id: 'mapping', label: 'Mapping', description: 'Mapping columns to required fields' },
  { id: 'processing', label: 'Processing', description: 'Importing holdings into portfolio' },
  { id: 'completed', label: 'Completed', description: 'Import completed successfully' },
];

export interface UploadProgressTrackerProps {
  currentStep: UploadStep;
  estimatedTimeRemaining?: number; // seconds
  error?: string | null;
}

export const UploadProgressTracker: React.FC<UploadProgressTrackerProps> = ({
  currentStep,
  estimatedTimeRemaining,
  error,
}) => {
  const getCurrentStepIndex = () => {
    if (currentStep === 'failed') return -1;
    return STEPS.findIndex((step) => step.id === currentStep);
  };

  const currentIndex = getCurrentStepIndex();
  const isFailed = currentStep === 'failed';

  const getStepStatus = (stepIndex: number): 'completed' | 'current' | 'pending' | 'failed' => {
    if (isFailed && stepIndex === currentIndex) return 'failed';
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  return (
    <Card data-testid="upload-progress-tracker">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Upload Progress</CardTitle>
          {estimatedTimeRemaining && estimatedTimeRemaining > 0 && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span data-testid="upload-time-remaining">
                ~{formatTime(estimatedTimeRemaining)} remaining
              </span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-0">
          {STEPS.map((step, index) => {
            const status = getStepStatus(index);
            const isLast = index === STEPS.length - 1;

            return (
              <div key={step.id} data-testid={`upload-step-${step.id}`}>
                <div className="flex items-start gap-4 py-4">
                  {/* Icon */}
                  <div className="relative flex-shrink-0">
                    {status === 'completed' ? (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[hsl(var(--success))]/10">
                        <CheckCircle2 className="h-5 w-5 text-[hsl(var(--success))]" />
                      </div>
                    ) : status === 'current' ? (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                        <Loader2 className="h-5 w-5 text-primary animate-spin" />
                      </div>
                    ) : status === 'failed' ? (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-destructive/10">
                        <XCircle className="h-5 w-5 text-destructive" />
                      </div>
                    ) : (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                        <Circle className="h-5 w-5 text-muted-foreground" />
                      </div>
                    )}

                    {/* Connector line */}
                    {!isLast && (
                      <div
                        className={cn(
                          'absolute left-1/2 top-10 -translate-x-1/2 w-0.5 h-16',
                          status === 'completed' ? 'bg-[hsl(var(--success))]' : 'bg-border'
                        )}
                      />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 pt-1">
                    <p
                      className={cn(
                        'text-sm font-medium',
                        status === 'completed'
                          ? 'text-[hsl(var(--success))]'
                          : status === 'current'
                          ? 'text-primary'
                          : status === 'failed'
                          ? 'text-destructive'
                          : 'text-muted-foreground'
                      )}
                      data-testid={`upload-step-${step.id}-label`}
                    >
                      {step.label}
                    </p>
                    <p
                      className="text-xs text-muted-foreground mt-0.5"
                      data-testid={`upload-step-${step.id}-description`}
                    >
                      {status === 'failed' && error ? error : step.description}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};