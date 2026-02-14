import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { Separator } from '../components/ui/separator';
import {
  Bell, BellOff, Check, Trash2, RefreshCw, Database, TrendingUp, AlertTriangle, Info,
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ALERT_ICONS = {
  new_scenario: <Database className="h-4 w-4 text-blue-600" />,
  major_revision: <AlertTriangle className="h-4 w-4 text-amber-500" />,
  trend_change: <TrendingUp className="h-4 w-4 text-emerald-600" />,
  new_source: <Info className="h-4 w-4 text-violet-600" />,
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ user_id: 'default_user' });
      if (showUnreadOnly) params.set('unread_only', 'true');
      const r = await fetch(`${API_URL}/api/v1/analysis/alerts?${params}`);
      setAlerts(await r.json());
    } catch {}
    setLoading(false);
  }, [showUnreadOnly]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  const markRead = async (id) => {
    await fetch(`${API_URL}/api/v1/analysis/alerts/${id}/read`, { method: 'PATCH' });
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
  };

  const markAllRead = async () => {
    const unread = alerts.filter(a => !a.is_read);
    await Promise.all(unread.map(a => fetch(`${API_URL}/api/v1/analysis/alerts/${a.id}/read`, { method: 'PATCH' })));
    setAlerts(prev => prev.map(a => ({ ...a, is_read: true })));
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  // Generate sample alerts if none exist
  const generateSampleAlerts = async () => {
    const samples = [
      { alert_type: 'new_scenario', title: 'New NGFS Phase V scenarios available', message: '6 new scenarios added from NGFS Phase V data release. Net Zero 2050, Below 2C, and Delayed Transition updated.' },
      { alert_type: 'major_revision', title: 'IPCC AR6 data revised', message: 'IPCC AR6 SSP pathways updated with corrected temperature projections for SSP2-4.5 and SSP3-7.0.' },
      { alert_type: 'trend_change', title: 'Carbon price trend shift detected', message: 'EU ETS carbon price projections for 2030 increased by 15% across multiple scenarios. Review affected portfolios.' },
      { alert_type: 'new_source', title: 'New data source: CMIP6 Physical Risk', message: 'Physical risk scenarios from CMIP6 now available with temperature, sea level, and precipitation projections.' },
      { alert_type: 'new_scenario', title: 'IEA WEO 2024 scenarios synced', message: 'Latest IEA World Energy Outlook scenarios (NZE, APS, STEPS) have been synchronized with updated 2050 projections.' },
    ];
    for (const s of samples) {
      await fetch(`${API_URL}/api/v1/analysis/alerts`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...s, user_id: 'default_user' }),
      }).catch(() => {});
    }
    fetchAlerts();
  };

  return (
    <div className="p-6 space-y-6" data-testid="alerts-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            Scenario Alerts
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white text-xs ml-1">{unreadCount}</Badge>
            )}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Notifications for scenario updates, data revisions, and trend changes</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowUnreadOnly(!showUnreadOnly)} data-testid="toggle-unread">
            {showUnreadOnly ? <Bell className="h-3 w-3 mr-1" /> : <BellOff className="h-3 w-3 mr-1" />}
            {showUnreadOnly ? 'Show All' : 'Unread Only'}
          </Button>
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={markAllRead} data-testid="mark-all-read">
              <Check className="h-3 w-3 mr-1" />Mark All Read
            </Button>
          )}
          {alerts.length === 0 && (
            <Button size="sm" onClick={generateSampleAlerts} data-testid="generate-alerts">
              <RefreshCw className="h-3 w-3 mr-1" />Generate Sample Alerts
            </Button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <RefreshCw className="h-5 w-5 animate-spin mr-2" />Loading...
        </div>
      ) : alerts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Bell className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No alerts yet</p>
            <p className="text-xs mt-1">You'll be notified when scenarios are updated or new data is available</p>
            <Button variant="outline" size="sm" className="mt-3" onClick={generateSampleAlerts}>
              Generate Sample Alerts
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2" data-testid="alerts-list">
          {alerts.map(alert => (
            <Card key={alert.id} className={`transition-all ${!alert.is_read ? 'border-l-4 border-l-primary bg-primary/[0.02]' : 'opacity-75'}`}
              data-testid={`alert-${alert.id}`}>
              <CardContent className="py-3 px-4 flex items-start gap-3">
                <div className="mt-0.5 shrink-0">
                  {ALERT_ICONS[alert.alert_type] || <Info className="h-4 w-4 text-muted-foreground" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <h3 className={`text-sm ${!alert.is_read ? 'font-semibold' : 'font-medium'}`}>{alert.title}</h3>
                    <Badge variant="outline" className="text-[9px] shrink-0">{alert.alert_type.replace(/_/g, ' ')}</Badge>
                    {!alert.is_read && <Badge className="bg-blue-500 text-white text-[9px]">New</Badge>}
                  </div>
                  {alert.message && <p className="text-xs text-muted-foreground line-clamp-2">{alert.message}</p>}
                  <p className="text-[10px] text-muted-foreground mt-1">{new Date(alert.created_at).toLocaleString()}</p>
                </div>
                {!alert.is_read && (
                  <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={() => markRead(alert.id)}
                    data-testid={`mark-read-${alert.id}`}>
                    <Check className="h-3 w-3" />
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
