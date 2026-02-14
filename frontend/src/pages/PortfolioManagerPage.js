import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { toast } from 'sonner';
import {
  Upload, FileText, Plus, Trash2, Save, CheckCircle, AlertTriangle,
  RefreshCw, Edit3, Download,
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PortfolioManagerPage() {
  const [activeTab, setActiveTab] = useState('upload');
  const [portfolios, setPortfolios] = useState([]);

  // Upload state
  const [csvContent, setCsvContent] = useState('');
  const [parseResult, setParseResult] = useState(null);
  const [portfolioName, setPortfolioName] = useState('');
  const [creating, setCreating] = useState(false);

  // Editor state
  const [editPortfolioId, setEditPortfolioId] = useState('');
  const [editAssets, setEditAssets] = useState([]);
  const [editLoading, setEditLoading] = useState(false);

  const fetchPortfolios = useCallback(async () => {
    const r = await fetch(`${API_URL}/api/portfolios`);
    const d = await r.json();
    setPortfolios(d.portfolios || []);
  }, []);

  useEffect(() => { fetchPortfolios(); }, [fetchPortfolios]);

  // ---- Upload ----
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setCsvContent(ev.target.result);
    reader.readAsText(file);
  };

  const handleParse = async () => {
    if (!csvContent.trim()) return;
    try {
      const r = await fetch(`${API_URL}/api/v1/analysis/portfolio-upload/parse`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: csvContent }),
      });
      setParseResult(await r.json());
      toast.success('File parsed successfully');
    } catch { toast.error('Parse failed'); }
  };

  const handleCreate = async () => {
    if (!parseResult?.assets?.length || !portfolioName.trim()) return;
    setCreating(true);
    try {
      const r = await fetch(`${API_URL}/api/v1/analysis/portfolio-upload/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: portfolioName, description: 'Uploaded via CSV', assets: parseResult.assets }),
      });
      const d = await r.json();
      toast.success(`Portfolio created: ${d.num_assets} assets`);
      setParseResult(null); setCsvContent(''); setPortfolioName('');
      fetchPortfolios();
    } catch { toast.error('Create failed'); }
    finally { setCreating(false); }
  };

  // ---- Editor ----
  const loadPortfolioForEdit = async (id) => {
    setEditLoading(true);
    setEditPortfolioId(id);
    try {
      const r = await fetch(`${API_URL}/api/portfolios/${id}`);
      const d = await r.json();
      setEditAssets(d.assets || []);
    } catch { toast.error('Failed to load'); }
    finally { setEditLoading(false); }
  };

  const removeAsset = (assetId) => {
    setEditAssets(prev => prev.filter(a => a.id !== assetId));
  };

  const addNewAsset = () => {
    setEditAssets(prev => [...prev, {
      id: crypto.randomUUID(), asset_type: 'Bond',
      company: { name: 'New Company', sector: 'Power Generation', subsector: null },
      exposure: 1000000, market_value: 1000000,
      base_pd: 0.02, base_lgd: 0.45, rating: 'BBB', maturity_years: 5,
    }]);
  };

  const updateAssetField = (assetId, field, value) => {
    setEditAssets(prev => prev.map(a => {
      if (a.id !== assetId) return a;
      if (field.startsWith('company.')) {
        const subField = field.split('.')[1];
        return { ...a, company: { ...a.company, [subField]: value } };
      }
      return { ...a, [field]: value };
    }));
  };

  const savePortfolio = async () => {
    if (!editPortfolioId) return;
    try {
      await fetch(`${API_URL}/api/portfolios/${editPortfolioId}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assets: editAssets }),
      });
      toast.success('Portfolio saved');
      fetchPortfolios();
    } catch { toast.error('Save failed'); }
  };

  return (
    <div className="p-6 space-y-6" data-testid="portfolio-manager-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <FileText className="h-6 w-6 text-primary" />
          Portfolio Manager
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Upload, create, and edit portfolios</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="upload" data-testid="tab-upload"><Upload className="h-3 w-3 mr-1" />Upload</TabsTrigger>
          <TabsTrigger value="editor" data-testid="tab-editor"><Edit3 className="h-3 w-3 mr-1" />Editor</TabsTrigger>
          <TabsTrigger value="list" data-testid="tab-list"><FileText className="h-3 w-3 mr-1" />Portfolios ({portfolios.length})</TabsTrigger>
        </TabsList>

        {/* ---- Upload Tab ---- */}
        <TabsContent value="upload" className="space-y-4 mt-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Upload CSV File</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="border-2 border-dashed rounded-lg p-6 text-center hover:border-primary/50 transition-colors"
                data-testid="upload-zone">
                <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-muted-foreground mb-2">Drag & drop a CSV file or click to browse</p>
                <input type="file" accept=".csv,.txt" onChange={handleFileChange}
                  className="block mx-auto text-sm" data-testid="file-input" />
              </div>
              <p className="text-xs text-muted-foreground">
                Required columns: <strong>name</strong> (company), <strong>sector</strong>, <strong>exposure</strong>.
                Optional: asset_type, rating, pd, lgd, maturity, market_value
              </p>
              {csvContent && (
                <>
                  <Textarea value={csvContent} onChange={e => setCsvContent(e.target.value)}
                    rows={6} className="font-mono text-xs" placeholder="Paste CSV content..." data-testid="csv-textarea" />
                  <Button onClick={handleParse} data-testid="parse-btn">
                    <CheckCircle className="h-4 w-4 mr-1" />Validate & Parse
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {/* Parse results */}
          {parseResult && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  Validation Results
                  <Badge variant={parseResult.errors.length > 0 ? 'destructive' : 'default'}>
                    {parseResult.valid_rows} valid / {parseResult.total_rows} total
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {parseResult.errors.length > 0 && (
                  <div className="space-y-1">
                    {parseResult.errors.map((e, i) => (
                      <div key={i} className="text-xs text-destructive flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" />Row {e.row}: {e.error}
                      </div>
                    ))}
                  </div>
                )}
                <div className="text-xs text-muted-foreground">
                  Column mapping: {Object.entries(parseResult.column_mapping || {}).map(([k, v]) => `${k}→${v}`).join(', ')}
                </div>

                {parseResult.assets.length > 0 && (
                  <>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Company</TableHead><TableHead>Sector</TableHead>
                          <TableHead>Type</TableHead><TableHead className="text-right">Exposure</TableHead>
                          <TableHead>Rating</TableHead><TableHead className="text-right">PD</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {parseResult.assets.slice(0, 20).map((a, i) => (
                          <TableRow key={i}>
                            <TableCell className="text-xs">{a.company?.name}</TableCell>
                            <TableCell className="text-xs">{a.company?.sector}</TableCell>
                            <TableCell className="text-xs">{a.asset_type}</TableCell>
                            <TableCell className="text-xs text-right tabular-nums">${a.exposure?.toLocaleString()}</TableCell>
                            <TableCell className="text-xs">{a.rating}</TableCell>
                            <TableCell className="text-xs text-right tabular-nums">{(a.base_pd * 100).toFixed(2)}%</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>

                    <div className="flex items-center gap-3">
                      <Input placeholder="Portfolio name..." value={portfolioName} onChange={e => setPortfolioName(e.target.value)}
                        className="max-w-xs" data-testid="portfolio-name-input" />
                      <Button onClick={handleCreate} disabled={!portfolioName.trim() || creating} data-testid="create-portfolio-btn">
                        {creating ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Save className="h-4 w-4 mr-1" />}
                        Create Portfolio
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ---- Editor Tab ---- */}
        <TabsContent value="editor" className="space-y-4 mt-4">
          <div className="flex items-center gap-3">
            <Select value={editPortfolioId} onValueChange={loadPortfolioForEdit}>
              <SelectTrigger className="w-[300px]" data-testid="edit-portfolio-select">
                <SelectValue placeholder="Select portfolio to edit..." />
              </SelectTrigger>
              <SelectContent>
                {portfolios.map(p => <SelectItem key={p.id} value={p.id}>{p.name} ({p.num_assets} assets)</SelectItem>)}
              </SelectContent>
            </Select>
            {editPortfolioId && (
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={addNewAsset} data-testid="add-asset-btn">
                  <Plus className="h-3 w-3 mr-1" />Add Asset
                </Button>
                <Button size="sm" onClick={savePortfolio} data-testid="save-portfolio-btn">
                  <Save className="h-3 w-3 mr-1" />Save
                </Button>
              </div>
            )}
          </div>

          {editLoading ? (
            <p className="text-center py-8 text-muted-foreground"><RefreshCw className="h-4 w-4 inline animate-spin mr-2" />Loading...</p>
          ) : editAssets.length > 0 ? (
            <Card>
              <CardContent className="pt-4 overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Company</TableHead><TableHead>Sector</TableHead><TableHead>Type</TableHead>
                      <TableHead>Exposure</TableHead><TableHead>Rating</TableHead><TableHead>PD</TableHead>
                      <TableHead>LGD</TableHead><TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {editAssets.map(a => (
                      <TableRow key={a.id}>
                        <TableCell>
                          <Input value={a.company?.name || ''} className="h-7 text-xs w-32"
                            onChange={e => updateAssetField(a.id, 'company.name', e.target.value)} />
                        </TableCell>
                        <TableCell>
                          <select value={a.company?.sector || ''} className="h-7 text-xs border rounded px-1"
                            onChange={e => updateAssetField(a.id, 'company.sector', e.target.value)}>
                            {['Power Generation', 'Oil & Gas', 'Metals & Mining', 'Automotive', 'Airlines', 'Real Estate'].map(s =>
                              <option key={s} value={s}>{s}</option>)}
                          </select>
                        </TableCell>
                        <TableCell>
                          <select value={a.asset_type || 'Bond'} className="h-7 text-xs border rounded px-1"
                            onChange={e => updateAssetField(a.id, 'asset_type', e.target.value)}>
                            {['Bond', 'Loan', 'Equity'].map(t => <option key={t} value={t}>{t}</option>)}
                          </select>
                        </TableCell>
                        <TableCell>
                          <Input type="number" value={a.exposure || 0} className="h-7 text-xs w-24"
                            onChange={e => updateAssetField(a.id, 'exposure', Number(e.target.value))} />
                        </TableCell>
                        <TableCell>
                          <Input value={a.rating || 'BBB'} className="h-7 text-xs w-14"
                            onChange={e => updateAssetField(a.id, 'rating', e.target.value)} />
                        </TableCell>
                        <TableCell>
                          <Input type="number" step="0.001" value={a.base_pd || 0.02} className="h-7 text-xs w-16"
                            onChange={e => updateAssetField(a.id, 'base_pd', Number(e.target.value))} />
                        </TableCell>
                        <TableCell>
                          <Input type="number" step="0.01" value={a.base_lgd || 0.45} className="h-7 text-xs w-16"
                            onChange={e => updateAssetField(a.id, 'base_lgd', Number(e.target.value))} />
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => removeAsset(a.id)}>
                            <Trash2 className="h-3 w-3 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : editPortfolioId ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No assets. <Button variant="link" onClick={addNewAsset}>Add one</Button></p>
            </div>
          ) : null}
        </TabsContent>

        {/* ---- List Tab ---- */}
        <TabsContent value="list" className="space-y-3 mt-4">
          {portfolios.map(p => (
            <Card key={p.id} data-testid={`portfolio-card-${p.id}`}>
              <CardContent className="py-3 px-4 flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-sm">{p.name}</h3>
                  <p className="text-xs text-muted-foreground">{p.num_assets} assets — ${p.total_exposure?.toLocaleString()} exposure</p>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" onClick={() => { setEditPortfolioId(p.id); loadPortfolioForEdit(p.id); setActiveTab('editor'); }}>
                    <Edit3 className="h-3 w-3 mr-1" />Edit
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
