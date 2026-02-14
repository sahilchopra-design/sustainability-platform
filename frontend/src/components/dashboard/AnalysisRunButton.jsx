import React from 'react';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { Play, Loader2, CheckCircle, AlertCircle, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';
import { toast } from 'sonner';

export function AnalysisRunButton({
  onRun,
  running = false,
  progress = 0,
  error = null,
  disabled = false,
  portfolioName = null,
  scenarioCount = 0,
  className,
}) {
  const handleClick = async () => {
    if (running || disabled) return;
    
    if (scenarioCount === 0) {
      toast.error('Please select at least one scenario');
      return;
    }
    
    toast.info('Starting analysis...', { id: 'analysis-toast' });
    
    try {
      const result = await onRun?.();
      if (result) {
        toast.success('Analysis completed!', { id: 'analysis-toast' });
      }
    } catch (err) {
      toast.error(err.message || 'Analysis failed', { id: 'analysis-toast' });
    }
  };

  const getButtonContent = () => {
    if (running) {
      return (
        <>
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          Running Analysis...
        </>
      );
    }

    if (error) {
      return (
        <>
          <AlertCircle className="h-4 w-4 mr-2" />
          Retry Analysis
        </>
      );
    }

    return (
      <>
        <Play className="h-4 w-4 mr-2" />
        Run Scenario Analysis
      </>
    );
  };

  const getTooltipContent = () => {
    if (disabled && !portfolioName) {
      return 'Select a portfolio to run analysis';
    }
    if (disabled && scenarioCount === 0) {
      return 'Select at least one scenario';
    }
    if (running) {
      return `Analysis in progress: ${progress}%`;
    }
    return `Analyze ${portfolioName || 'portfolio'} with ${scenarioCount} scenario${scenarioCount !== 1 ? 's' : ''}`;
  };

  return (
    <div className={cn("space-y-2", className)}>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="lg"
              onClick={handleClick}
              disabled={disabled || running}
              className={cn(
                "w-full transition-all",
                error && "bg-destructive hover:bg-destructive/90",
                !running && !error && !disabled && "bg-primary hover:bg-primary/90"
              )}
              data-testid="run-analysis-button"
            >
              {getButtonContent()}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{getTooltipContent()}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Progress Bar */}
      {running && (
        <div className="space-y-1" data-testid="analysis-progress">
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-muted-foreground text-center tabular-nums">
            {progress}% complete
          </p>
        </div>
      )}

      {/* Quick Info */}
      {!running && portfolioName && scenarioCount > 0 && (
        <p className="text-xs text-muted-foreground text-center flex items-center justify-center gap-1">
          <Zap className="h-3 w-3" />
          {portfolioName} × {scenarioCount} scenario{scenarioCount !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  );
}

// Compact variant for inline use
export function AnalysisRunButtonCompact({
  onRun,
  running = false,
  progress = 0,
  disabled = false,
  className,
}) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            onClick={onRun}
            disabled={disabled || running}
            size="sm"
            className={className}
            data-testid="run-analysis-button-compact"
          >
            {running ? (
              <>
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                {progress}%
              </>
            ) : (
              <>
                <Play className="h-3 w-3 mr-1" />
                Run
              </>
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{running ? `Analysis: ${progress}%` : 'Run scenario analysis'}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
