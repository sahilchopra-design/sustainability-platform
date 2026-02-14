import React, { useState } from 'react';
import { Search, Building2, DollarSign, CheckCircle2, ChevronRight, ChevronLeft } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Card } from '../ui/card';
import { Separator } from '../ui/separator';
import { Holding, Counterparty } from '../../types/portfolio';
import { cn } from '../../lib/utils';

export interface AddHoldingModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (holding: Omit<Holding, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  portfolioId: string;
  portfolioCurrency: string;
  loading?: boolean;
}

interface FormData {
  counterparty_id: string;
  counterparty_name: string;
  exposure: string;
  currency: string;
  sector: string;
  rating: string;
  lei: string;
  isin: string;
  country: string;
  maturity_date: string;
}

const MOCK_COUNTERPARTIES: Counterparty[] = [
  { id: '1', name: 'Apple Inc.', lei: '549300K5QBQCPLFYX235', sector: 'Technology', country: 'US', rating: 'AA+' },
  { id: '2', name: 'Microsoft Corporation', lei: '549300594IRCS9TKH748', sector: 'Technology', country: 'US', rating: 'AAA' },
  { id: '3', name: 'JPMorgan Chase', lei: '8I5DZWZKVSZI1NUHU748', sector: 'Financials', country: 'US', rating: 'A+' },
  { id: '4', name: 'Toyota Motor Corp', lei: '549300GRWV24PZOKTV09', sector: 'Consumer Discretionary', country: 'JP', rating: 'AA-' },
  { id: '5', name: 'Volkswagen AG', lei: '529900D6BX41YIOOHU306', sector: 'Consumer Discretionary', country: 'DE', rating: 'BBB+' },
];

export const AddHoldingModal: React.FC<AddHoldingModalProps> = ({
  open,
  onClose,
  onAdd,
  portfolioId,
  portfolioCurrency,
  loading = false,
}) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCounterparty, setSelectedCounterparty] = useState<Counterparty | null>(null);
  const [formData, setFormData] = useState<FormData>({
    counterparty_id: '',
    counterparty_name: '',
    exposure: '',
    currency: portfolioCurrency,
    sector: '',
    rating: '',
    lei: '',
    isin: '',
    country: '',
    maturity_date: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const filteredCounterparties = MOCK_COUNTERPARTIES.filter((cp) =>
    cp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (cp.lei && cp.lei.includes(searchQuery.toUpperCase()))
  );

  const handleSelectCounterparty = (counterparty: Counterparty) => {
    setSelectedCounterparty(counterparty);
    setFormData((prev) => ({
      ...prev,
      counterparty_id: counterparty.id,
      counterparty_name: counterparty.name,
      lei: counterparty.lei || '',
      sector: counterparty.sector || '',
      country: counterparty.country || '',
      rating: counterparty.rating || '',
    }));
    setStep(2);
  };

  const validateStep2 = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};
    
    if (!formData.exposure || parseFloat(formData.exposure) <= 0) {
      newErrors.exposure = 'Exposure must be greater than 0';
    }
    
    if (!formData.currency) {
      newErrors.currency = 'Currency is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (step === 2 && !validateStep2()) {
      return;
    }
    setStep((prev) => Math.min(3, prev + 1) as 1 | 2 | 3);
  };

  const handleBack = () => {
    setStep((prev) => Math.max(1, prev - 1) as 1 | 2 | 3);
  };

  const handleSubmit = async () => {
    if (!validateStep2()) return;
    
    await onAdd({
      portfolio_id: portfolioId,
      counterparty_id: formData.counterparty_id,
      counterparty_name: formData.counterparty_name,
      exposure: parseFloat(formData.exposure),
      currency: formData.currency,
      sector: formData.sector || undefined,
      rating: formData.rating || undefined,
      lei: formData.lei || undefined,
      isin: formData.isin || undefined,
      country: formData.country || undefined,
      maturity_date: formData.maturity_date || undefined,
      lgd: undefined,
      pd: undefined,
    } as Omit<Holding, 'id' | 'created_at' | 'updated_at'>);
    
    handleClose();
  };

  const handleClose = () => {
    setStep(1);
    setSearchQuery('');
    setSelectedCounterparty(null);
    setFormData({
      counterparty_id: '',
      counterparty_name: '',
      exposure: '',
      currency: portfolioCurrency,
      sector: '',
      rating: '',
      lei: '',
      isin: '',
      country: '',
      maturity_date: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl" data-testid="add-holding-modal">
        <DialogHeader>
          <DialogTitle>Add New Holding</DialogTitle>
          <DialogDescription>
            Step {step} of 3: {step === 1 ? 'Select Counterparty' : step === 2 ? 'Enter Details' : 'Review'}
          </DialogDescription>
        </DialogHeader>

        {/* Step Indicator */}
        <div className="flex items-center gap-2 mb-6">
          {[1, 2, 3].map((s) => (
            <React.Fragment key={s}>
              <div
                className={cn(
                  'flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium',
                  s < step
                    ? 'bg-[hsl(var(--success))] text-white'
                    : s === step
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                )}
                data-testid={`step-indicator-${s}`}
              >
                {s < step ? <CheckCircle2 className="h-4 w-4" /> : s}
              </div>
              {s < 3 && (
                <div className={cn('flex-1 h-0.5', s < step ? 'bg-[hsl(var(--success))]' : 'bg-muted')} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Step 1: Search and Select Counterparty */}
        {step === 1 && (
          <div className="space-y-4" data-testid="step-1-select-counterparty">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name or LEI..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                data-testid="counterparty-search-input"
              />
            </div>

            <ScrollArea className="h-[400px] border rounded-lg">
              <div className="p-2 space-y-2">
                {filteredCounterparties.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Building2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                    <p>No counterparties found</p>
                  </div>
                ) : (
                  filteredCounterparties.map((cp) => (
                    <Card
                      key={cp.id}
                      className="p-4 cursor-pointer transition-colors hover:bg-accent"
                      onClick={() => handleSelectCounterparty(cp)}
                      data-testid={`counterparty-option-${cp.id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{cp.name}</p>
                          {cp.lei && (
                            <p className="text-xs text-muted-foreground font-mono mt-0.5">
                              LEI: {cp.lei}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            {cp.sector && (
                              <Badge variant="outline" className="text-xs">
                                {cp.sector}
                              </Badge>
                            )}
                            {cp.country && (
                              <Badge variant="secondary" className="text-xs">
                                {cp.country}
                              </Badge>
                            )}
                            {cp.rating && (
                              <Badge variant="outline" className="text-xs">
                                {cp.rating}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Step 2: Enter Holding Details */}
        {step === 2 && (
          <div className="space-y-4" data-testid="step-2-enter-details">
            <Card className="p-4 bg-accent/50">
              <div className="flex items-center gap-3">
                <Building2 className="h-10 w-10 p-2 rounded-lg bg-primary/10 text-primary" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{formData.counterparty_name}</p>
                  {formData.lei && (
                    <p className="text-xs text-muted-foreground font-mono">{formData.lei}</p>
                  )}
                </div>
              </div>
            </Card>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="exposure">Exposure Amount *</Label>
                <Input
                  id="exposure"
                  type="number"
                  step="0.01"
                  placeholder="1000000"
                  value={formData.exposure}
                  onChange={(e) => setFormData({ ...formData, exposure: e.target.value })}
                  className={errors.exposure ? 'border-destructive' : ''}
                  data-testid="exposure-input"
                />
                {errors.exposure && (
                  <p className="text-xs text-destructive">{errors.exposure}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="currency">Currency *</Label>
                <Select
                  value={formData.currency}
                  onValueChange={(value) => setFormData({ ...formData, currency: value })}
                >
                  <SelectTrigger id="currency" data-testid="currency-select">
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

              <div className="space-y-2">
                <Label htmlFor="isin">ISIN</Label>
                <Input
                  id="isin"
                  placeholder="US0378331005"
                  value={formData.isin}
                  onChange={(e) => setFormData({ ...formData, isin: e.target.value })}
                  data-testid="isin-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="maturity_date">Maturity Date</Label>
                <Input
                  id="maturity_date"
                  type="date"
                  value={formData.maturity_date}
                  onChange={(e) => setFormData({ ...formData, maturity_date: e.target.value })}
                  data-testid="maturity-date-input"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Review and Confirm */}
        {step === 3 && (
          <div className="space-y-4" data-testid="step-3-review">
            <Card className="p-6 bg-accent/30">
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <Building2 className="h-12 w-12 p-3 rounded-lg bg-primary/10 text-primary" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{formData.counterparty_name}</h3>
                    {formData.lei && (
                      <p className="text-sm text-muted-foreground font-mono mt-1">{formData.lei}</p>
                    )}
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground mb-1">Exposure</p>
                    <p className="font-semibold text-lg tabular-nums">
                      {parseFloat(formData.exposure).toLocaleString()} {formData.currency}
                    </p>
                  </div>
                  {formData.sector && (
                    <div>
                      <p className="text-muted-foreground mb-1">Sector</p>
                      <p className="font-medium">{formData.sector}</p>
                    </div>
                  )}
                  {formData.rating && (
                    <div>
                      <p className="text-muted-foreground mb-1">Rating</p>
                      <p className="font-medium">{formData.rating}</p>
                    </div>
                  )}
                  {formData.country && (
                    <div>
                      <p className="text-muted-foreground mb-1">Country</p>
                      <p className="font-medium">{formData.country}</p>
                    </div>
                  )}
                  {formData.isin && (
                    <div>
                      <p className="text-muted-foreground mb-1">ISIN</p>
                      <p className="font-mono text-xs">{formData.isin}</p>
                    </div>
                  )}
                  {formData.maturity_date && (
                    <div>
                      <p className="text-muted-foreground mb-1">Maturity</p>
                      <p className="font-medium">
                        {new Date(formData.maturity_date).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between gap-2 pt-4">
          <Button
            variant="outline"
            onClick={step === 1 ? handleClose : handleBack}
            disabled={loading}
            data-testid="modal-back-button"
          >
            {step === 1 ? 'Cancel' : (
              <>
                <ChevronLeft className="h-4 w-4 mr-2" />
                Back
              </>
            )}
          </Button>
          <Button
            onClick={step === 3 ? handleSubmit : handleNext}
            disabled={loading || (step === 1 && !selectedCounterparty)}
            data-testid="modal-next-button"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Adding...
              </>
            ) : step === 3 ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Add Holding
              </>
            ) : (
              <>
                Continue
                <ChevronRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};