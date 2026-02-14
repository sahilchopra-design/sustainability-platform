import React, { useState, useEffect } from 'react';
import { Save, X, AlertCircle } from 'lucide-react';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../ui/sheet';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { Holding } from '../../types/portfolio';

export interface EditHoldingDrawerProps {
  open: boolean;
  onClose: () => void;
  holding: Holding | null;
  onUpdate: (holdingId: string, updates: Partial<Holding>) => Promise<void>;
  loading?: boolean;
}

interface FormData {
  exposure: string;
  currency: string;
  sector: string;
  rating: string;
  lei: string;
  isin: string;
  country: string;
  maturity_date: string;
  lgd: string;
  pd: string;
}

export const EditHoldingDrawer: React.FC<EditHoldingDrawerProps> = ({
  open,
  onClose,
  holding,
  onUpdate,
  loading = false,
}) => {
  const [formData, setFormData] = useState<FormData>({
    exposure: '',
    currency: '',
    sector: '',
    rating: '',
    lei: '',
    isin: '',
    country: '',
    maturity_date: '',
    lgd: '',
    pd: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize form data when holding changes
  useEffect(() => {
    if (holding) {
      setFormData({
        exposure: String(holding.exposure),
        currency: holding.currency,
        sector: holding.sector || '',
        rating: holding.rating || '',
        lei: holding.lei || '',
        isin: holding.isin || '',
        country: holding.country || '',
        maturity_date: holding.maturity_date || '',
        lgd: holding.lgd ? String(holding.lgd) : '',
        pd: holding.pd ? String(holding.pd) : '',
      });
      setErrors({});
      setHasChanges(false);
    }
  }, [holding]);

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
    // Clear error for this field
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.exposure || parseFloat(formData.exposure) <= 0) {
      newErrors.exposure = 'Exposure must be greater than 0';
    }

    if (!formData.currency) {
      newErrors.currency = 'Currency is required';
    }

    if (formData.lgd && (parseFloat(formData.lgd) < 0 || parseFloat(formData.lgd) > 1)) {
      newErrors.lgd = 'LGD must be between 0 and 1';
    }

    if (formData.pd && (parseFloat(formData.pd) < 0 || parseFloat(formData.pd) > 1)) {
      newErrors.pd = 'PD must be between 0 and 1';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!holding || !validate()) return;

    const updates: Partial<Holding> = {};

    // Only include changed fields
    if (formData.exposure !== String(holding.exposure)) {
      updates.exposure = parseFloat(formData.exposure);
    }
    if (formData.currency !== holding.currency) {
      updates.currency = formData.currency;
    }
    if (formData.sector !== (holding.sector || '')) {
      updates.sector = formData.sector || undefined;
    }
    if (formData.rating !== (holding.rating || '')) {
      updates.rating = formData.rating || undefined;
    }
    if (formData.lei !== (holding.lei || '')) {
      updates.lei = formData.lei || undefined;
    }
    if (formData.isin !== (holding.isin || '')) {
      updates.isin = formData.isin || undefined;
    }
    if (formData.country !== (holding.country || '')) {
      updates.country = formData.country || undefined;
    }
    if (formData.maturity_date !== (holding.maturity_date || '')) {
      updates.maturity_date = formData.maturity_date || undefined;
    }
    if (formData.lgd !== (holding.lgd ? String(holding.lgd) : '')) {
      updates.lgd = formData.lgd ? parseFloat(formData.lgd) : undefined;
    }
    if (formData.pd !== (holding.pd ? String(holding.pd) : '')) {
      updates.pd = formData.pd ? parseFloat(formData.pd) : undefined;
    }

    await onUpdate(holding.id, updates);
  };

  if (!holding) return null;

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="sm:max-w-lg overflow-y-auto" data-testid="edit-holding-drawer">
        <SheetHeader>
          <SheetTitle>Edit Holding</SheetTitle>
          <SheetDescription>{holding.counterparty_name}</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Counterparty Info (Read-only) */}
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-sm font-medium mb-1">Counterparty</p>
            <p className="text-sm text-muted-foreground">{holding.counterparty_name}</p>
            {holding.lei && (
              <p className="text-xs font-mono text-muted-foreground mt-1">{holding.lei}</p>
            )}
          </div>

          <Separator />

          {/* Exposure Details */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Exposure Details</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-exposure">
                  Exposure Amount <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="edit-exposure"
                  type="number"
                  step="0.01"
                  value={formData.exposure}
                  onChange={(e) => handleChange('exposure', e.target.value)}
                  className={errors.exposure ? 'border-destructive' : ''}
                  data-testid="edit-exposure-input"
                />
                {errors.exposure && (
                  <p className="text-xs text-destructive">{errors.exposure}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-currency">
                  Currency <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={formData.currency}
                  onValueChange={(value) => handleChange('currency', value)}
                >
                  <SelectTrigger id="edit-currency" data-testid="edit-currency-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                    <SelectItem value="JPY">JPY</SelectItem>
                    <SelectItem value="CHF">CHF</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator />

          {/* Classification */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Classification</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-sector">Sector</Label>
                <Input
                  id="edit-sector"
                  placeholder="e.g., Technology"
                  value={formData.sector}
                  onChange={(e) => handleChange('sector', e.target.value)}
                  data-testid="edit-sector-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-rating">Credit Rating</Label>
                <Input
                  id="edit-rating"
                  placeholder="e.g., AAA"
                  value={formData.rating}
                  onChange={(e) => handleChange('rating', e.target.value)}
                  data-testid="edit-rating-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-country">Country</Label>
                <Input
                  id="edit-country"
                  placeholder="e.g., US"
                  value={formData.country}
                  onChange={(e) => handleChange('country', e.target.value)}
                  data-testid="edit-country-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-maturity">Maturity Date</Label>
                <Input
                  id="edit-maturity"
                  type="date"
                  value={formData.maturity_date}
                  onChange={(e) => handleChange('maturity_date', e.target.value)}
                  data-testid="edit-maturity-input"
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Identifiers */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Identifiers</h3>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit-lei">LEI</Label>
                <Input
                  id="edit-lei"
                  placeholder="20-character LEI code"
                  value={formData.lei}
                  onChange={(e) => handleChange('lei', e.target.value)}
                  maxLength={20}
                  data-testid="edit-lei-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-isin">ISIN</Label>
                <Input
                  id="edit-isin"
                  placeholder="12-character ISIN"
                  value={formData.isin}
                  onChange={(e) => handleChange('isin', e.target.value)}
                  maxLength={12}
                  data-testid="edit-isin-input"
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Risk Parameters */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Risk Parameters</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-pd">Probability of Default (PD)</Label>
                <Input
                  id="edit-pd"
                  type="number"
                  step="0.001"
                  min="0"
                  max="1"
                  placeholder="0.050"
                  value={formData.pd}
                  onChange={(e) => handleChange('pd', e.target.value)}
                  className={errors.pd ? 'border-destructive' : ''}
                  data-testid="edit-pd-input"
                />
                {errors.pd && (
                  <p className="text-xs text-destructive">{errors.pd}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-lgd">Loss Given Default (LGD)</Label>
                <Input
                  id="edit-lgd"
                  type="number"
                  step="0.001"
                  min="0"
                  max="1"
                  placeholder="0.450"
                  value={formData.lgd}
                  onChange={(e) => handleChange('lgd', e.target.value)}
                  className={errors.lgd ? 'border-destructive' : ''}
                  data-testid="edit-lgd-input"
                />
                {errors.lgd && (
                  <p className="text-xs text-destructive">{errors.lgd}</p>
                )}
              </div>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                Risk parameters are optional and will be auto-calculated if left blank
              </AlertDescription>
            </Alert>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={loading}
              data-testid="drawer-cancel-button"
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={loading || !hasChanges}
              data-testid="drawer-save-button"
            >
              {loading ? (
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
        </div>
      </SheetContent>
    </Sheet>
  );
};
