/**
 * ScenarioTabs Component
 * Tab interface for managing scenarios
 */

import React from 'react';
import { X, Plus, Copy } from 'lucide-react';

export const ScenarioTabs = ({
  scenarios = [],
  activeScenarioId,
  onSelect,
  onCreate,
  onDuplicate,
  onDelete
}) => {
  return (
    <div className="border-b border-slate-200" data-testid="scenario-tabs">
      <div className="flex items-center gap-1 overflow-x-auto">
        {scenarios.map((scenario) => (
          <div
            key={scenario.id}
            className={`
              group relative flex items-center gap-2 px-4 py-3 text-sm font-medium
              cursor-pointer whitespace-nowrap transition-colors
              ${activeScenarioId === scenario.id
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
              }
            `}
            onClick={() => onSelect?.(scenario.id)}
            data-testid={`scenario-tab-${scenario.id}`}
          >
            <span>{scenario.name}</span>
            {scenario.is_default && (
              <span className="text-xs text-slate-400">(Default)</span>
            )}
            
            {/* Hover Actions */}
            <div className="hidden group-hover:flex items-center gap-1 ml-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDuplicate?.(scenario.id);
                }}
                className="p-1 rounded hover:bg-slate-200 transition-colors"
                title="Duplicate scenario"
              >
                <Copy className="w-3 h-3" />
              </button>
              {!scenario.is_default && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete?.(scenario.id);
                  }}
                  className="p-1 rounded hover:bg-rose-100 hover:text-rose-600 transition-colors"
                  title="Delete scenario"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        ))}
        
        <button
          onClick={onCreate}
          className="flex items-center gap-1 px-4 py-3 text-sm font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-colors"
          data-testid="create-scenario-btn"
        >
          <Plus className="w-4 h-4" />
          <span>New Scenario</span>
        </button>
      </div>
    </div>
  );
};

export default ScenarioTabs;
