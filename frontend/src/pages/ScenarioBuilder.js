import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { ScrollArea } from '../components/ui/scroll-area';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'sonner';
import { 
  GitBranch, 
  Plus, 
  Check, 
  X, 
  Send, 
  Eye, 
  Trash2, 
  RefreshCw,
  FileText,
  Clock,
  Settings,
  TrendingUp,
  Thermometer,
  DollarSign,
  Factory
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SCENARIO_TYPE_LABELS = {
  net_zero_2050: 'Net Zero 2050',
  delayed_transition: 'Delayed Transition',
  below_2c: 'Below 2°C',
  ndc: 'NDCs',
  current_policies: 'Current Policies',
  fragmented_world: 'Fragmented World',
};

const STATUS_COLORS = {
  draft: 'bg-muted text-muted-foreground',
  pending_approval: 'bg-warning/20 text-warning',
  approved: 'bg-success/20 text-success',
  rejected: 'bg-destructive/20 text-destructive',
  archived: 'bg-muted text-muted-foreground',
};

export default function ScenarioBuilder() {
  const [scenarios, setScenarios] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [forkDialogOpen, setForkDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [forkName, setForkName] = useState('');
  const [forkDescription, setForkDescription] = useState('');
  const [activeTab, setActiveTab] = useState('templates');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [scenariosRes, templatesRes, sourcesRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/scenarios`),
        fetch(`${API_URL}/api/v1/scenarios/templates`),
        fetch(`${API_URL}/api/v1/scenarios/ngfs/sources`),
      ]);
      
      const scenariosData = await scenariosRes.json();
      const templatesData = await templatesRes.json();
      const sourcesData = await sourcesRes.json();
      
      setScenarios(scenariosData);
      setTemplates(templatesData);
      setSources(sourcesData);
    } catch (error) {
      toast.error('Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      // Create source if none exists
      if (sources.length === 0) {
        await fetch(`${API_URL}/api/v1/scenarios/ngfs/sources?name=NGFS%20Phase%20V&version=5.0`, {
          method: 'POST',
        });
      }
      
      // Get sources again
      const sourcesRes = await fetch(`${API_URL}/api/v1/scenarios/ngfs/sources`);
      const sourcesData = await sourcesRes.json();
      
      if (sourcesData.length > 0) {
        await fetch(`${API_URL}/api/v1/scenarios/ngfs/sync?source_id=${sourcesData[0].id}`, {
          method: 'POST',
        });
        toast.success('NGFS scenarios synced successfully');
        fetchData();
      }
    } catch (error) {
      toast.error('Failed to sync NGFS data');
    } finally {
      setSyncing(false);
    }
  };

  const handleFork = async (templateId) => {
    if (!forkName.trim()) {
      toast.error('Please enter a name for the new scenario');
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/api/v1/scenarios/${templateId}/fork`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_name: forkName,
          description: forkDescription,
          created_by: 'current_user',
        }),
      });
      
      if (res.ok) {
        toast.success('Scenario forked successfully');
        setForkDialogOpen(false);
        setForkName('');
        setForkDescription('');
        setSelectedScenario(null);
        fetchData();
        setActiveTab('custom');
      }
    } catch (error) {
      toast.error('Failed to fork scenario');
    }
  };

  const handleSubmitForApproval = async (scenarioId) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/scenarios/${scenarioId}/submit-for-approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          submitted_by: 'current_user',
          notes: 'Ready for review',
        }),
      });
      
      if (res.ok) {
        toast.success('Submitted for approval');
        fetchData();
      }
    } catch (error) {
      toast.error('Failed to submit for approval');
    }
  };

  const handleApprove = async (scenarioId, approved) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/scenarios/${scenarioId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved,
          approved_by: 'risk_manager',
          notes: approved ? 'Approved for use' : 'Please review parameters',
        }),
      });
      
      if (res.ok) {
        toast.success(approved ? 'Scenario approved' : 'Scenario rejected');
        fetchData();
      }
    } catch (error) {
      toast.error('Failed to update approval status');
    }
  };

  const handlePublish = async (scenarioId) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/scenarios/${scenarioId}/publish`, {
        method: 'POST',
      });
      
      if (res.ok) {
        toast.success('Scenario published');
        fetchData();
      }
    } catch (error) {
      toast.error('Failed to publish scenario');
    }
  };

  const handleDelete = async (scenarioId) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/scenarios/${scenarioId}`, {
        method: 'DELETE',
      });
      
      if (res.ok) {
        toast.success('Scenario deleted');
        fetchData();
      }
    } catch (error) {
      toast.error('Failed to delete scenario');
    }
  };

  const customScenarios = scenarios.filter(s => s.source !== 'ngfs');
  const pendingApproval = scenarios.filter(s => s.approval_status === 'pending_approval');

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="scenario-builder-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight font-['Space_Grotesk']">
            Scenario Builder
          </h1>
          <p className="text-muted-foreground mt-1">
            Create and manage climate risk scenarios based on NGFS data
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={handleSync}
            disabled={syncing}
            data-testid="sync-ngfs-button"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync NGFS Data'}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card data-testid="stat-templates">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums">{templates.length}</p>
                <p className="text-sm text-muted-foreground">NGFS Templates</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card data-testid="stat-custom">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-accent/10 rounded-lg">
                <Settings className="h-5 w-5 text-accent" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums">{customScenarios.length}</p>
                <p className="text-sm text-muted-foreground">Custom Scenarios</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card data-testid="stat-pending">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-warning/10 rounded-lg">
                <Clock className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums">{pendingApproval.length}</p>
                <p className="text-sm text-muted-foreground">Pending Approval</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card data-testid="stat-sources">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-success/10 rounded-lg">
                <TrendingUp className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums">{sources.length}</p>
                <p className="text-sm text-muted-foreground">Data Sources</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList data-testid="scenario-tabs">
          <TabsTrigger value="templates" data-testid="tab-templates">
            NGFS Templates ({templates.length})
          </TabsTrigger>
          <TabsTrigger value="custom" data-testid="tab-custom">
            Custom Scenarios ({customScenarios.length})
          </TabsTrigger>
          <TabsTrigger value="approval" data-testid="tab-approval">
            Approval Queue ({pendingApproval.length})
          </TabsTrigger>
        </TabsList>

        {/* NGFS Templates */}
        <TabsContent value="templates" className="space-y-4">
          {templates.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No NGFS Templates</h3>
                <p className="text-muted-foreground mb-4">
                  Click "Sync NGFS Data" to import the latest scenarios
                </p>
                <Button onClick={handleSync} disabled={syncing}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                  Sync Now
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {templates.map(template => (
                <ScenarioTemplateCard
                  key={template.id}
                  template={template}
                  onFork={() => {
                    setSelectedScenario(template);
                    setForkName(`${template.name} - Custom`);
                    setForkDialogOpen(true);
                  }}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Custom Scenarios */}
        <TabsContent value="custom" className="space-y-4">
          {customScenarios.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Settings className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Custom Scenarios</h3>
                <p className="text-muted-foreground mb-4">
                  Fork an NGFS template to create your first custom scenario
                </p>
                <Button onClick={() => setActiveTab('templates')}>
                  Browse Templates
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Table data-testid="custom-scenarios-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Base Scenario</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {customScenarios.map(scenario => (
                  <TableRow key={scenario.id} data-testid={`scenario-row-${scenario.id}`}>
                    <TableCell className="font-medium">{scenario.name}</TableCell>
                    <TableCell>
                      {scenario.base_scenario_id ? (
                        <Badge variant="outline">Forked</Badge>
                      ) : (
                        <Badge variant="outline">Custom</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={STATUS_COLORS[scenario.approval_status]}>
                        {scenario.approval_status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>v{scenario.current_version}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(scenario.updated_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {scenario.approval_status === 'draft' && (
                          <>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleSubmitForApproval(scenario.id)}
                              data-testid={`submit-${scenario.id}`}
                            >
                              <Send className="h-4 w-4 mr-1" />
                              Submit
                            </Button>
                            <Button 
                              size="sm" 
                              variant="ghost"
                              onClick={() => handleDelete(scenario.id)}
                              data-testid={`delete-${scenario.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                        {scenario.approval_status === 'approved' && !scenario.is_published && (
                          <Button 
                            size="sm"
                            onClick={() => handlePublish(scenario.id)}
                            data-testid={`publish-${scenario.id}`}
                          >
                            Publish
                          </Button>
                        )}
                        {scenario.is_published && (
                          <Badge variant="default" className="bg-success text-success-foreground">
                            Published
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>

        {/* Approval Queue */}
        <TabsContent value="approval" className="space-y-4">
          {pendingApproval.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Check className="h-12 w-12 mx-auto text-success mb-4" />
                <h3 className="text-lg font-medium mb-2">All Caught Up!</h3>
                <p className="text-muted-foreground">
                  No scenarios pending approval
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {pendingApproval.map(scenario => (
                <ApprovalCard
                  key={scenario.id}
                  scenario={scenario}
                  onApprove={() => handleApprove(scenario.id, true)}
                  onReject={() => handleApprove(scenario.id, false)}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Fork Dialog */}
      <Dialog open={forkDialogOpen} onOpenChange={setForkDialogOpen}>
        <DialogContent data-testid="fork-dialog">
          <DialogHeader>
            <DialogTitle>Fork Scenario</DialogTitle>
            <DialogDescription>
              Create a customized version of "{selectedScenario?.name}"
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="fork-name">Scenario Name</Label>
              <Input
                id="fork-name"
                value={forkName}
                onChange={(e) => setForkName(e.target.value)}
                placeholder="My Custom Scenario"
                data-testid="fork-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fork-description">Description</Label>
              <Textarea
                id="fork-description"
                value={forkDescription}
                onChange={(e) => setForkDescription(e.target.value)}
                placeholder="Describe the purpose of this scenario..."
                data-testid="fork-description-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setForkDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => handleFork(selectedScenario?.id)} data-testid="fork-confirm-button">
              <GitBranch className="h-4 w-4 mr-2" />
              Fork Scenario
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Template Card Component
function ScenarioTemplateCard({ template, onFork }) {
  const params = template.parameters || {};
  
  return (
    <Card className="hover:shadow-md transition-shadow" data-testid={`template-${template.id}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{template.name}</CardTitle>
            <CardDescription className="mt-1">{template.description}</CardDescription>
          </div>
          <Badge variant="outline" className="text-xs">
            {SCENARIO_TYPE_LABELS[template.ngfs_scenario_type] || template.ngfs_scenario_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Key Parameters Preview */}
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground text-xs">Carbon Price 2050</p>
              <p className="font-medium tabular-nums">
                ${params.carbon_price?.['2050'] || 'N/A'}/tCO2
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Thermometer className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground text-xs">Temp 2050</p>
              <p className="font-medium tabular-nums">
                +{params.temperature_pathway?.['2050'] || 'N/A'}°C
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground text-xs">GDP Impact</p>
              <p className="font-medium tabular-nums">
                {params.gdp_impact?.['2050'] || 'N/A'}%
              </p>
            </div>
          </div>
        </div>
        
        {/* Sectoral Impact Preview */}
        <div className="pt-2 border-t">
          <p className="text-xs text-muted-foreground mb-2">Sectoral Multipliers</p>
          <div className="flex flex-wrap gap-1">
            {params.sectoral_multipliers && Object.entries(params.sectoral_multipliers).slice(0, 5).map(([sector, mult]) => (
              <Badge key={sector} variant="secondary" className="text-xs">
                {sector}: {mult}x
              </Badge>
            ))}
          </div>
        </div>

        <Button className="w-full" onClick={onFork} data-testid={`fork-${template.id}`}>
          <GitBranch className="h-4 w-4 mr-2" />
          Fork & Customize
        </Button>
      </CardContent>
    </Card>
  );
}

// Approval Card Component
function ApprovalCard({ scenario, onApprove, onReject }) {
  return (
    <Card data-testid={`approval-${scenario.id}`}>
      <CardContent className="py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-medium">{scenario.name}</h3>
            <p className="text-sm text-muted-foreground mt-1">{scenario.description}</p>
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              <span>Submitted by: {scenario.submitted_by}</span>
              <span>•</span>
              <span>Version {scenario.current_version}</span>
              <span>•</span>
              <span>{new Date(scenario.submitted_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={onReject}
              data-testid={`reject-${scenario.id}`}
            >
              <X className="h-4 w-4 mr-1" />
              Reject
            </Button>
            <Button 
              size="sm"
              onClick={onApprove}
              data-testid={`approve-${scenario.id}`}
            >
              <Check className="h-4 w-4 mr-1" />
              Approve
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
