import React, { useState } from 'react';
import { Save, Settings, Clock, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { Portfolio } from '../../types/portfolio';

export interface PortfolioEditorProps {
  portfolio: Portfolio;
  onUpdate: (updates: Partial<Portfolio>) => Promise<void>;
  saving?: boolean;
  children?: React.ReactNode;
}

export const PortfolioEditor: React.FC<PortfolioEditorProps> = ({
  portfolio,
  onUpdate,
  saving = false,
  children,
}) => {
  const [formData, setFormData] = useState({
    name: portfolio.name,
    description: portfolio.description || '',
    currency: portfolio.currency,
  });
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    const updates: Partial<Portfolio> = {};
    if (formData.name !== portfolio.name) updates.name = formData.name;
    if (formData.description !== (portfolio.description || '')) updates.description = formData.description;
    if (formData.currency !== portfolio.currency) updates.currency = formData.currency;

    if (Object.keys(updates).length > 0) {
      await onUpdate(updates);
      setHasChanges(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="portfolio-editor">
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4" data-testid="portfolio-tabs">
          <TabsTrigger value="overview" data-testid="tab-overview">
            <BarChart3 className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="holdings" data-testid="tab-holdings">
            Holdings
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">
            <Clock className="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
          <TabsTrigger value="settings" data-testid="tab-settings">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="space-y-6">
            <Card data-testid="portfolio-details-card">
              <CardHeader>
                <CardTitle>Portfolio Details</CardTitle>
                <CardDescription>Edit portfolio name and description</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="portfolio-name">Name *</Label>
                  <Input
                    id="portfolio-name"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    data-testid="portfolio-name-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="portfolio-description">Description</Label>
                  <Textarea
                    id="portfolio-description"
                    value={formData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    rows={3}
                    placeholder="Optional description of this portfolio..."
                    data-testid="portfolio-description-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="portfolio-currency">Base Currency *</Label>
                  <Input
                    id="portfolio-currency"
                    value={formData.currency}
                    onChange={(e) => handleChange('currency', e.target.value.toUpperCase())}
                    maxLength={3}
                    placeholder="USD"
                    data-testid="portfolio-currency-input"
                  />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="text-xs text-muted-foreground">
                    Created: {new Date(portfolio.created_at).toLocaleDateString()}
                    {' • '}
                    Updated: {new Date(portfolio.updated_at).toLocaleDateString()}
                  </div>
                  <Button
                    onClick={handleSave}
                    disabled={!hasChanges || saving}
                    data-testid="save-portfolio-button"
                  >
                    {saving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Metrics will be passed as children */}
            {children}
          </div>
        </TabsContent>

        {/* Holdings Tab - Content passed as children */}
        <TabsContent value="holdings" className="mt-6">
          {children}
        </TabsContent>

        {/* History Tab - Content passed as children */}
        <TabsContent value="history" className="mt-6">
          {children}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Portfolio Settings</CardTitle>
              <CardDescription>Advanced portfolio configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Additional settings and configurations will be available here.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};