/**
 * RiskHeatMap Component
 * Displays risk matrix for carbon projects
 */

import React from 'react';

export const RiskHeatMap = ({ risks = [] }) => {
  const getColor = (impact, probability) => {
    const matrix = {
      Low: {
        Low: 'bg-emerald-400',
        Medium: 'bg-emerald-300',
        High: 'bg-amber-300'
      },
      Medium: {
        Low: 'bg-emerald-300',
        Medium: 'bg-amber-300',
        High: 'bg-amber-400'
      },
      High: {
        Low: 'bg-amber-300',
        Medium: 'bg-amber-400',
        High: 'bg-rose-400'
      },
      Critical: {
        Low: 'bg-amber-400',
        Medium: 'bg-rose-400',
        High: 'bg-rose-500'
      }
    };
    return matrix[impact]?.[probability] || 'bg-slate-200';
  };

  const getTextColor = (impact, probability) => {
    if (impact === 'High' || impact === 'Critical') return 'text-white';
    if (impact === 'Medium' && probability === 'High') return 'text-white';
    return 'text-slate-800';
  };

  const impactLevels = ['Low', 'Medium', 'High'];
  const probabilityLevels = ['Low', 'Medium', 'High'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6" data-testid="risk-heatmap">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        Risk Heat Map
      </h3>

      <div className="grid grid-cols-4 gap-2">
        {/* Header Row */}
        <div className="text-xs font-medium text-slate-500">Impact →</div>
        {impactLevels.map((level) => (
          <div key={level} className="text-xs font-medium text-slate-500 text-center">
            {level}
          </div>
        ))}

        {/* Data Rows */}
        {probabilityLevels.map((probability) => (
          <React.Fragment key={probability}>
            <div className="text-xs font-medium text-slate-500 flex items-center">
              {probability} Prob
            </div>
            {impactLevels.map((impact) => {
              const risk = risks.find(
                (r) => r.impact === impact && r.probability === probability
              );
              return (
                <div
                  key={`${impact}-${probability}`}
                  className={`
                    h-12 rounded-md flex items-center justify-center text-xs font-medium
                    transition-all duration-200 hover:scale-105 cursor-pointer
                    ${risk ? getColor(impact, probability) : 'bg-slate-100'}
                    ${risk ? getTextColor(impact, probability) : 'text-slate-400'}
                  `}
                  title={risk ? `${risk.category}: ${risk.score}/100` : 'No risk'}
                  data-testid={`risk-cell-${impact}-${probability}`}
                >
                  {risk ? risk.category.substring(0, 6) : '-'}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-emerald-400" />
          <span>Low Risk</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-amber-400" />
          <span>Medium Risk</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-rose-500" />
          <span>High Risk</span>
        </div>
      </div>
    </div>
  );
};

export default RiskHeatMap;
