/**
 * Scheduled Reports Manager Component
 * UI for managing automated report exports
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '../../components/ui/dialog';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../components/ui/table';
import { 
  Calendar, Clock, Mail, FileText, Plus, Trash2, 
  Edit, Play, Pause, Settings, FileSpreadsheet
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const REPORT_TYPES = [
  { value: 'portfolio_analytics', label: 'Portfolio Analytics' },
  { value: 'carbon_credits', label: 'Carbon Credits' },
  { value: 'stranded_assets', label: 'Stranded Assets' },
  { value: 'nature_risk', label: 'Nature Risk' },
  { value: 'sustainability', label: 'Sustainability' },
  { value: 'valuation', label: 'Real Estate Valuation' },
  { value: 'scenario_analysis', label: 'Scenario Analysis' },
];

const FREQUENCIES = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
];

const FORMATS = [
  { value: 'pdf', label: 'PDF' },
  { value: 'excel', label: 'Excel' },
];

export function ScheduledReportsManager() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingReport, setEditingReport] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    report_type: '',
    frequency: 'weekly',
    format: 'pdf',
    recipients: '',
  });

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/scheduled-reports`);
      const data = await response.json();
      setReports(data.items || []);
    } catch (err) {
      console.error('Error fetching reports:', err);
      toast.error('Failed to load scheduled reports');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.report_type || !formData.recipients) {
      toast.error('Please fill in all required fields');
      return;
    }

    const payload = {
      ...formData,
      recipients: formData.recipients.split(',').map(e => e.trim()).filter(Boolean),
    };

    try {
      const method = editingReport ? 'PATCH' : 'POST';
      const url = editingReport 
        ? `${API_URL}/api/v1/scheduled-reports/${editingReport.id}`
        : `${API_URL}/api/v1/scheduled-reports`;

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error('Failed to save report');

      toast.success(editingReport ? 'Report updated' : 'Report scheduled');
      setDialogOpen(false);
      resetForm();
      fetchReports();
    } catch (err) {
      console.error('Error saving report:', err);
      toast.error('Failed to save scheduled report');
    }
  };

  const handleDelete = async (reportId) => {
    if (!window.confirm('Are you sure you want to delete this scheduled report?')) return;

    try {
      await fetch(`${API_URL}/api/v1/scheduled-reports/${reportId}`, { method: 'DELETE' });
      toast.success('Report deleted');
      fetchReports();
    } catch (err) {
      console.error('Error deleting report:', err);
      toast.error('Failed to delete report');
    }
  };

  const handleToggle = async (reportId) => {
    try {
      await fetch(`${API_URL}/api/v1/scheduled-reports/${reportId}/toggle`, { method: 'POST' });
      fetchReports();
    } catch (err) {
      console.error('Error toggling report:', err);
      toast.error('Failed to toggle report');
    }
  };

  const handleEdit = (report) => {
    setEditingReport(report);
    setFormData({
      name: report.name,
      report_type: report.report_type,
      frequency: report.frequency,
      format: report.format,
      recipients: report.recipients.join(', '),
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setEditingReport(null);
    setFormData({
      name: '',
      report_type: '',
      frequency: 'weekly',
      format: 'pdf',
      recipients: '',
    });
  };

  const getTypeLabel = (type) => REPORT_TYPES.find(t => t.value === type)?.label || type;
  const getFrequencyLabel = (freq) => FREQUENCIES.find(f => f.value === freq)?.label || freq;

  return (
    <Card data-testid="scheduled-reports-manager">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              Scheduled Reports
            </CardTitle>
            <CardDescription>
              Automate recurring report exports to stakeholders
            </CardDescription>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button data-testid="add-schedule-btn">
                <Plus className="h-4 w-4 mr-2" />
                Add Schedule
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>
                  {editingReport ? 'Edit Scheduled Report' : 'Schedule New Report'}
                </DialogTitle>
                <DialogDescription>
                  Configure automated report delivery
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Report Name *</Label>
                  <Input 
                    placeholder="e.g., Weekly Portfolio Summary"
                    value={formData.name}
                    onChange={e => setFormData({...formData, name: e.target.value})}
                    data-testid="schedule-name-input"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Report Type *</Label>
                  <Select 
                    value={formData.report_type}
                    onValueChange={v => setFormData({...formData, report_type: v})}
                  >
                    <SelectTrigger data-testid="schedule-type-select">
                      <SelectValue placeholder="Select report type" />
                    </SelectTrigger>
                    <SelectContent>
                      {REPORT_TYPES.map(t => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Frequency</Label>
                    <Select 
                      value={formData.frequency}
                      onValueChange={v => setFormData({...formData, frequency: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FREQUENCIES.map(f => (
                          <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Format</Label>
                    <Select 
                      value={formData.format}
                      onValueChange={v => setFormData({...formData, format: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FORMATS.map(f => (
                          <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Recipients (comma separated) *</Label>
                  <Input 
                    placeholder="email1@example.com, email2@example.com"
                    value={formData.recipients}
                    onChange={e => setFormData({...formData, recipients: e.target.value})}
                    data-testid="schedule-recipients-input"
                  />
                  <p className="text-xs text-slate-500">
                    Enter email addresses separated by commas
                  </p>
                </div>
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSubmit} data-testid="schedule-save-btn">
                  {editingReport ? 'Update' : 'Schedule'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-500">Loading...</div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12 bg-slate-50 rounded-lg">
            <Calendar className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-600 font-medium">No scheduled reports yet</p>
            <p className="text-sm text-slate-500 mt-1">
              Create your first automated report schedule
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Frequency</TableHead>
                <TableHead>Recipients</TableHead>
                <TableHead>Next Run</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reports.map(report => (
                <TableRow key={report.id} data-testid={`report-row-${report.id}`}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {report.format === 'pdf' ? (
                        <FileText className="h-4 w-4 text-red-500" />
                      ) : (
                        <FileSpreadsheet className="h-4 w-4 text-green-600" />
                      )}
                      {report.name}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{getTypeLabel(report.report_type)}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Clock className="h-3 w-3 text-slate-400" />
                      {getFrequencyLabel(report.frequency)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Mail className="h-3 w-3 text-slate-400" />
                      {report.recipients.length} recipient(s)
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-slate-600">
                    {report.next_run 
                      ? new Date(report.next_run).toLocaleDateString()
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <Badge className={report.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'}>
                      {report.is_active ? 'Active' : 'Paused'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button 
                        variant="ghost" 
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleToggle(report.id)}
                      >
                        {report.is_active ? (
                          <Pause className="h-4 w-4 text-amber-500" />
                        ) : (
                          <Play className="h-4 w-4 text-green-500" />
                        )}
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleEdit(report)}
                      >
                        <Edit className="h-4 w-4 text-blue-500" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleDelete(report.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

export default ScheduledReportsManager;
