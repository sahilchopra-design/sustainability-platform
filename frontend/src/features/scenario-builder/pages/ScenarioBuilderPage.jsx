/**
 * ScenarioBuilderPage — full-page layout for the Scenario Builder v2.
 *
 * Layout:
 *  ┌──────────────────────────────────────┬───────────────────┐
 *  │  5-step wizard (ScenarioBuilderWizard)│  Right sidebar    │
 *  │                                      │  - Version History│
 *  │                                      │  - Impact Preview │
 *  │                                      │  - Compare        │
 *  │                                      │  - NGFS Browser   │
 *  └──────────────────────────────────────┴───────────────────┘
 *
 * Route: /scenario-builder-v2
 */
import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { useScenarioBuilder }         from '../hooks/useScenarioBuilder';
import { ScenarioBuilderWizard }      from '../components/ScenarioBuilderWizard';
import { ScenarioVersionTimeline }    from '../components/ScenarioVersionTimeline';
import { ScenarioImpactPreviewPanel } from '../components/ScenarioImpactPreviewPanel';
import { ScenarioComparisonView }     from '../components/ScenarioComparisonView';
import { NGFSDataBrowser }            from '../components/NGFSDataBrowser';
import { ALL_PARAMETERS }             from '../data/ngfsData';

// ─── Sidebar tab ids ──────────────────────────────────────────────────────────

const SIDEBAR_TABS = [
  { id: 'history',  label: 'History',  icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { id: 'impact',   label: 'Impact',   icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { id: 'compare',  label: 'Compare',  icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { id: 'ngfs',     label: 'NGFS',     icon: 'M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2a15 15 0 014 10 15 15 0 01-4 10 15 15 0 01-4-10A15 15 0 0112 2z' },
];

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const cfg = {
    draft:     { label: 'Draft',     cls: 'bg-white/8 text-white/50 border-white/15' },
    published: { label: 'Published', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
    review:    { label: 'In Review', cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
    archived:  { label: 'Archived',  cls: 'bg-white/5 text-white/30 border-white/10' },
  };
  const { label, cls } = cfg[status] ?? cfg.draft;
  return (
    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${cls}`}>
      {label}
    </span>
  );
}

// ─── Page header ──────────────────────────────────────────────────────────────

function PageHeader({ scenario, isDirty, saving, onSave, onPublish, onNew }) {
  return (
    <div className="h-11 border-b border-white/[0.06] px-4 flex items-center gap-3 shrink-0 bg-[#070d1a]">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-[11px] text-white/35 min-w-0">
        <span
          onClick={onNew}
          className="hover:text-white/60 cursor-pointer transition-colors"
        >
          Scenarios
        </span>
        <span>/</span>
        <span className="text-white/70 font-medium truncate max-w-[200px]">
          {scenario.name || 'Untitled Scenario'}
        </span>
      </div>

      <StatusBadge status={scenario.status} />

      {isDirty && (
        <span className="text-[9px] text-amber-400/60 bg-amber-400/8 px-1.5 py-0.5 rounded border border-amber-400/15">
          Unsaved changes
        </span>
      )}

      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={onSave}
          disabled={saving || !isDirty}
          className="text-[11px] px-3 py-1.5 rounded border border-white/12 text-white/55 hover:border-cyan-500/30 hover:text-cyan-300 transition-colors disabled:opacity-30"
        >
          {saving ? 'Saving…' : 'Save Draft'}
        </button>
        <button
          onClick={onPublish}
          disabled={saving}
          className="text-[11px] px-3 py-1.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 transition-colors disabled:opacity-30 font-semibold"
        >
          Publish
        </button>
        <div className="w-px h-4 bg-white/10" />
        <button
          onClick={onNew}
          className="text-[11px] px-3 py-1.5 rounded border border-white/10 text-white/45 hover:text-white/70 hover:border-white/20 transition-colors"
        >
          + New
        </button>
      </div>
    </div>
  );
}

// ─── Right sidebar ────────────────────────────────────────────────────────────

function RightSidebar({ scenario, onRestoreVersion, onImportVariable }) {
  const [activeTab, setActiveTab] = useState('history');

  return (
    <aside className="w-80 shrink-0 border-l border-white/[0.06] bg-[#060c18] flex flex-col overflow-hidden">
      {/* Tab bar */}
      <div className="flex shrink-0 border-b border-white/[0.06]">
        {SIDEBAR_TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-[9px] font-semibold transition-colors border-b-2 ${
              activeTab === tab.id
                ? 'border-cyan-500 text-cyan-300'
                : 'border-transparent text-white/30 hover:text-white/55'
            }`}
            title={tab.label}
          >
            <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d={tab.icon} />
            </svg>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-3">
        {activeTab === 'history' && (
          <ScenarioVersionTimeline
            scenario={scenario}
            onRestoreVersion={onRestoreVersion}
          />
        )}
        {activeTab === 'impact' && (
          <ScenarioImpactPreviewPanel scenario={scenario} />
        )}
        {activeTab === 'compare' && (
          <ScenarioComparisonView currentScenario={scenario} />
        )}
        {activeTab === 'ngfs' && (
          <NGFSDataBrowser onImportVariable={onImportVariable} />
        )}
      </div>
    </aside>
  );
}

// ─── Publish success overlay ──────────────────────────────────────────────────

function PublishSuccessOverlay({ scenarioName, onDismiss, onViewGallery }) {
  return (
    <div className="absolute inset-0 bg-[#060c18]/90 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[#0d1526] border border-white/10 rounded-xl p-8 max-w-sm w-full text-center shadow-2xl">
        {/* Success icon */}
        <div className="w-14 h-14 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto mb-4">
          <svg className="h-7 w-7 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h3 className="text-base font-semibold text-white/90 mb-1">Scenario Published</h3>
        <p className="text-[12px] text-white/45 mb-6 leading-relaxed">
          <span className="text-cyan-300">"{scenarioName}"</span> is now available in the
          Scenario Gallery and can be used in portfolio analyses.
        </p>

        <div className="flex gap-3 justify-center">
          <button
            onClick={onDismiss}
            className="text-[12px] px-4 py-2 rounded border border-white/12 text-white/55 hover:text-white/75 transition-colors"
          >
            Continue Editing
          </button>
          <button
            onClick={onViewGallery}
            className="text-[12px] px-4 py-2 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 transition-colors font-semibold"
          >
            View Gallery
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function ScenarioBuilderPage() {
  const navigate   = useNavigate();
  const builder    = useScenarioBuilder();
  const [showPublishSuccess, setShowPublishSuccess] = useState(false);

  const { scenario, isDirty, saving, saveDraft, publish, restoreVersion, updateTrajectoryPoint } = builder;

  const handleSave = useCallback(async () => {
    await saveDraft();
  }, [saveDraft]);

  const handlePublish = useCallback(async () => {
    await publish();
    setShowPublishSuccess(true);
  }, [publish]);

  const handleNew = useCallback(() => {
    navigate('/scenario-gallery');
  }, [navigate]);

  const handleImportVariable = useCallback((paramId, ngfsFamily) => {
    // When a variable is imported from the NGFS browser, stamp the NGFS family's
    // trajectory for every year into the scenario parameter trajectory.
    const param = ALL_PARAMETERS.find(p => p.id === paramId);
    if (!param) return;
    const family = ngfsFamily === 'all' ? scenario.ngfsFamily || 'Orderly' : ngfsFamily;
    const traj = param.trajectories?.[family] ?? {};
    Object.entries(traj).forEach(([year, value]) => {
      updateTrajectoryPoint(paramId, parseFloat(year), value);
    });
  }, [scenario.ngfsFamily, updateTrajectoryPoint]);

  const handleWizardComplete = useCallback(() => {
    setShowPublishSuccess(true);
  }, []);

  return (
    <div className="flex flex-col h-full relative">
      {/* Page header */}
      <PageHeader
        scenario={scenario}
        isDirty={isDirty}
        saving={saving}
        onSave={handleSave}
        onPublish={handlePublish}
        onNew={handleNew}
      />

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Wizard — main area */}
        <div className="flex-1 overflow-y-auto p-4 min-w-0">
          <ScenarioBuilderWizard
            builderHook={builder}
            onComplete={handleWizardComplete}
          />
        </div>

        {/* Right sidebar */}
        <RightSidebar
          scenario={scenario}
          onRestoreVersion={restoreVersion}
          onImportVariable={handleImportVariable}
        />
      </div>

      {/* Publish success overlay */}
      {showPublishSuccess && (
        <PublishSuccessOverlay
          scenarioName={scenario.name || 'Untitled Scenario'}
          onDismiss={() => setShowPublishSuccess(false)}
          onViewGallery={() => navigate('/scenario-gallery')}
        />
      )}
    </div>
  );
}
