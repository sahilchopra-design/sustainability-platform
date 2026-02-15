/**
 * RiskSliders Component
 * Adjustable sliders for scenario risk parameters
 */

import React from 'react';
import { Slider } from '../../../../components/ui/slider';
import { Label } from '../../../../components/ui/label';
import { Info } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../../../../components/ui/tooltip';

const RISK_PARAMS = [
  {
    key: 'permanence_risk_pct',
    label: 'Permanence Risk',
    description: 'Risk that carbon sequestration may be reversed (e.g., forest fires, land-use change)',
    min: 0,
    max: 50,
    step: 1,
    unit: '%'
  },
  {
    key: 'delivery_risk_pct',
    label: 'Delivery Risk',
    description: 'Risk that project will not deliver expected credits on time',
    min: 0,
    max: 50,
    step: 1,
    unit: '%'
  },
  {
    key: 'regulatory_risk_pct',
    label: 'Regulatory Risk',
    description: 'Risk from changes in carbon market regulations or policies',
    min: 0,
    max: 50,
    step: 1,
    unit: '%'
  },
  {
    key: 'market_risk_pct',
    label: 'Market Risk',
    description: 'Risk from carbon price volatility and market conditions',
    min: 0,
    max: 50,
    step: 1,
    unit: '%'
  }
];

const PRICE_PARAMS = [
  {
    key: 'base_carbon_price_usd',
    label: 'Base Carbon Price',
    description: 'Current price per tonne of CO2 equivalent',
    min: 1,
    max: 100,
    step: 1,
    unit: '$/tCO2e'
  },
  {
    key: 'price_growth_rate_pct',
    label: 'Price Growth Rate',
    description: 'Expected annual increase in carbon prices',
    min: 0,
    max: 20,
    step: 0.5,
    unit: '%/yr'
  },
  {
    key: 'discount_rate_pct',
    label: 'Discount Rate',
    description: 'Rate used to discount future cash flows for NPV calculation',
    min: 1,
    max: 20,
    step: 0.5,
    unit: '%'
  }
];

export const RiskSliders = ({
  values = {},
  onChange,
  disabled = false
}) => {
  const handleChange = (key, newValue) => {
    if (onChange) {
      onChange({
        ...values,
        [key]: newValue[0]
      });
    }
  };

  const renderSlider = (param) => {
    const value = values[param.key] ?? param.min;
    
    return (
      <div key={param.key} className="space-y-2" data-testid={`slider-${param.key}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Label className="text-sm font-medium text-slate-700">
              {param.label}
            </Label>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="w-3.5 h-3.5 text-slate-400 cursor-help" />
                </TooltipTrigger>
                <TooltipContent className="max-w-[200px]">
                  <p className="text-xs">{param.description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <span className="text-sm font-semibold text-slate-900 tabular-nums">
            {value} {param.unit}
          </span>
        </div>
        <Slider
          value={[value]}
          onValueChange={(v) => handleChange(param.key, v)}
          min={param.min}
          max={param.max}
          step={param.step}
          disabled={disabled}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-slate-400">
          <span>{param.min}{param.unit}</span>
          <span>{param.max}{param.unit}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6" data-testid="risk-sliders">
      {/* Risk Parameters */}
      <div>
        <h4 className="text-sm font-semibold text-slate-900 mb-4">Risk Parameters</h4>
        <div className="space-y-6">
          {RISK_PARAMS.map(renderSlider)}
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-slate-100" />

      {/* Price & Financial Parameters */}
      <div>
        <h4 className="text-sm font-semibold text-slate-900 mb-4">Price & Financial</h4>
        <div className="space-y-6">
          {PRICE_PARAMS.map(renderSlider)}
        </div>
      </div>

      {/* Total Risk Summary */}
      <div className="border-t border-slate-100 pt-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-600">Total Risk Adjustment</span>
          <span className="text-lg font-bold text-slate-900 tabular-nums">
            {(
              (values.permanence_risk_pct || 0) +
              (values.delivery_risk_pct || 0) +
              (values.regulatory_risk_pct || 0) +
              (values.market_risk_pct || 0)
            ).toFixed(1)}%
          </span>
        </div>
        <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 transition-all duration-300"
            style={{
              width: `${Math.min(
                ((values.permanence_risk_pct || 0) +
                  (values.delivery_risk_pct || 0) +
                  (values.regulatory_risk_pct || 0) +
                  (values.market_risk_pct || 0)) / 2,
                100
              )}%`
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default RiskSliders;
