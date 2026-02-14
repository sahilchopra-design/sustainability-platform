import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent } from '../components/ui/tabs';
import { PortfolioEditor } from '../components/portfolio/PortfolioEditor';
import { HoldingsManager } from '../components/portfolio/HoldingsManager';
import { PortfolioMetricsSummary } from '../components/portfolio/PortfolioMetricsSummary';
import { AddHoldingModal } from '../components/portfolio/AddHoldingModal';
import { EditHoldingDrawer } from '../components/portfolio/EditHoldingDrawer';
import { ChangeHistoryLog } from '../components/portfolio/ChangeHistoryLog';
import { usePortfolioEditorStore } from '../store/portfolioEditorStore';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';

export default function PortfolioEditPage() {
  const { portfolioId } = useParams<{ portfolioId: string }>();
  const navigate = useNavigate();
  const [deleteConfirmId, setDeleteConfirmId] = React.useState<string | null>(null);
  const [bulkDeleteConfirm, setBulkDeleteConfirm] = React.useState(false);

  const {
    portfolio,
    holdings,
    metrics,
    changeLog,
    loading,
    saving,
    selectedHoldingIds,
    showAddModal,
    showEditDrawer,
    editingHolding,
    loadPortfolio,
    loadHoldings,
    refreshMetrics,
    loadChangeLog,
    updatePortfolio,
    addHolding,
    updateHolding,
    deleteHolding,
    bulkDeleteHoldings,
    setSelectedHoldingIds,
    openAddModal,
    closeAddModal,
    openEditDrawer,
    closeEditDrawer,
    undoChange,
    reset,
  } = usePortfolioEditorStore();

  // Load portfolio data on mount
  useEffect(() => {
    if (portfolioId) {
      loadPortfolio(portfolioId);
      loadHoldings(portfolioId);
      refreshMetrics(portfolioId);
      loadChangeLog(portfolioId);
    }

    return () => {
      reset();
    };
  }, [portfolioId]);

  const handleDelete = async (holdingId: string) => {
    await deleteHolding(holdingId);
    setDeleteConfirmId(null);
  };

  const handleBulkDelete = async () => {
    await bulkDeleteHoldings(selectedHoldingIds);
    setBulkDeleteConfirm(false);
  };

  const handleExport = (holdingIds: string[]) => {
    // TODO: Implement export functionality
    console.log('Export holdings:', holdingIds);
  };

  if (loading && !portfolio) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Alert variant="destructive" className="max-w-lg">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Portfolio not found. Please check the URL and try again.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className=\"min-h-screen bg-background\" data-testid=\"portfolio-edit-page\">
      {/* Hero band with gradient */}
      <div
        className=\"relative border-b border-border\"
        style={{
          background:
            'radial-gradient(1200px 600px at 12% 20%, hsla(199,89%,56%,0.18), transparent 55%), radial-gradient(900px 500px at 78% 30%, hsla(158,64%,38%,0.12), transparent 60%), linear-gradient(180deg, hsla(210,20%,98%,1), hsla(210,20%,98%,0.0))',
        }}
      >
        <div className=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8\">
          <Button
            variant=\"ghost\"
            size=\"sm\"
            className=\"mb-3 -ml-2\"
            onClick={() => navigate('/portfolios')}
            data-testid=\"back-to-portfolios-button\"
          >
            <ArrowLeft className=\"h-4 w-4 mr-2\" />
            Back to Portfolios
          </Button>
          <div>
            <h1
              className=\"text-4xl sm:text-5xl font-semibold tracking-tight text-foreground\"
              data-testid=\"portfolio-name-title\"
            >
              {portfolio.name}
            </h1>
            <p className=\"text-base md:text-lg text-muted-foreground mt-2\">
              {portfolio.description || 'Edit portfolio details and manage holdings'}
            </p>
            <p className=\"text-sm text-muted-foreground mt-1 font-mono\">
              ID: {portfolio.id}
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6\">
        <PortfolioEditor
          portfolio={portfolio}
          onUpdate={updatePortfolio}
          saving={saving}
        >
          {/* Override tab content based on active tab */}
          <Tabs defaultValue=\"overview\"  className=\"hidden\">
            <TabsContent value=\"overview\">
              <PortfolioMetricsSummary
                metrics={metrics}
                loading={loading}
                currency={portfolio.currency}
              />
            </TabsContent>

            <TabsContent value=\"holdings\">
              <HoldingsManager
                holdings={holdings}
                selectedIds={selectedHoldingIds}
                onSelectIds={setSelectedHoldingIds}
                onAdd={openAddModal}
                onEdit={openEditDrawer}
                onDelete={(id) => setDeleteConfirmId(id)}
                onBulkDelete={() => setBulkDeleteConfirm(true)}
                onExport={handleExport}
                loading={loading}
              />
            </TabsContent>

            <TabsContent value=\"history\">
              <ChangeHistoryLog
                changeLog={changeLog}
                loading={loading}
                onUndo={undoChange}
              />
            </TabsContent>
          </Tabs>

          {/* Render content based on the PortfolioEditor's active tab */}
          <PortfolioMetricsSummary
            metrics={metrics}
            loading={loading}
            currency={portfolio.currency}
          />
          <HoldingsManager
            holdings={holdings}
            selectedIds={selectedHoldingIds}
            onSelectIds={setSelectedHoldingIds}
            onAdd={openAddModal}
            onEdit={openEditDrawer}
            onDelete={(id) => setDeleteConfirmId(id)}
            onBulkDelete={() => setBulkDeleteConfirm(true)}
            onExport={handleExport}
            loading={loading}
          />
          <ChangeHistoryLog
            changeLog={changeLog}
            loading={loading}
            onUndo={undoChange}
          />
        </PortfolioEditor>
      </div>

      {/* Modals and Drawers */}
      <AddHoldingModal
        open={showAddModal}
        onClose={closeAddModal}
        onAdd={addHolding}
        portfolioId={portfolio.id}
        portfolioCurrency={portfolio.currency}
        loading={saving}
      />

      <EditHoldingDrawer
        open={showEditDrawer}
        onClose={closeEditDrawer}
        holding={editingHolding}
        onUpdate={updateHolding}
        loading={saving}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteConfirmId} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent data-testid=\"delete-holding-dialog\">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Holding?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove the holding from the portfolio. This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid=\"cancel-delete-button\">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
              className=\"bg-destructive hover:bg-destructive/90\"
              data-testid=\"confirm-delete-button\"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Bulk Delete Confirmation Dialog */}
      <AlertDialog open={bulkDeleteConfirm} onOpenChange={setBulkDeleteConfirm}>
        <AlertDialogContent data-testid=\"bulk-delete-dialog\">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectedHoldingIds.length} Holdings?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove {selectedHoldingIds.length} holdings from the portfolio.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid=\"cancel-bulk-delete-button\">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBulkDelete}
              className=\"bg-destructive hover:bg-destructive/90\"
              data-testid=\"confirm-bulk-delete-button\"
            >
              Delete All
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
