/**
 * ScenarioBuilderWizard — 5-step guided scenario creation.
 * Steps: 1. Template  2. Parameters  3. Trajectory  4. Preview  5. Review & Publish
 */
import React, { useState } from 'react';
import { ScenarioTemplateGallery } from './ScenarioTemplateGallery';
import { ParameterConfigurator }   from './ParameterConfigurator';
import { TrajectoryVisualizer }    from './TrajectoryVisualizer';
import { ScenarioImpactPreviewPanel } from './ScenarioImpactPreviewPanel';
import { ALL_PARAMETERS, NGFS_FAMILY_META } from '../data/ngfsData';

// ─── Step definitions ─────────────────────────────────────────────────────────

const STEPS = [
  { id: 'template',    label: 'Template',    icon: 'M4 6h16M4 10h16M4 14h10' },
  { id: 'parameters',  label: 'Parameters',  icon: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4' },
  { id: 'trajectory',  label: 'Trajectory',  icon: 'M3 3l18 18M3 21l18-18' },
  { id: 'preview',     label: 'Impact',      icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
  { id: 'review',      label: 'Publish',     icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
];

// ─── Step progress bar ────────────────────────────────────────────────────────

function StepProgress({ currentStep, onNavigate }) {
  const currentIdx = STEPS.findIndex(s => s.id === currentStep);

  return (
    <div className="flex items-center gap-0 mb-6" data-testid="wizard-progress">
      {STEPS.map((step, idx) => {
        const done    = idx < currentIdx;
        const active  = idx === currentIdx;
        const canJump = idx < currentIdx; // can only go back

        return (
          <React.Fragment key={step.id}>
            {/* Connector */}
            {idx > 0 && (
              <div className={`flex-1 h-px mx-1 transition-colors ${
                done ? 'bg-gray-500' : 'bg-white/8'
              }`} />
            )}

            {/* Step button */}
            <button
              onClick={() => canJump && onNavigate(step.id)}
              disabled={!canJump && !active}
              className={`flex flex-col items-center gap-1 group ${canJump ? 'cursor-pointer' : 'cursor-default'}`}
              data-testid={`wizard-step-${step.id}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all ${
                active
                  ? 'border-black bg-gray-200 shadow-[0_0_10px_rgba(34,211,238,0.25)]'
                  : done
                  ? 'border-black/60 bg-gray-100'
                  : 'border-black/15 bg-white/3'
              }`}>
                {done ? (
                  <svg className="h-3.5 w-3.5 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className={`h-3.5 w-3.5 ${active ? 'text-gray-800' : 'text-gray-500'}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={step.icon} />
                  </svg>
                )}
              </div>
              <span className={`text-[9px] font-medium ${
                active ? 'text-gray-800' : done ? 'text-gray-500' : 'text-gray-400'
              }`}>
                {step.label}
              </span>
            </button>
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ─── Step 1: Template ─────────────────────────────────────────────────────────

function StepTemplate({ onSelectTemplate, selectedTemplateId, onNext }) {
  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-[15px] font-semibold text-gray-900 mb-1">Choose a Starting Template</h3>
        <p className="text-[12px] text-gray-500">
          Select an official NGFS scenario or a custom stress test as your base. You can customise all parameters in the next step.
        </p>
      </div>

      <div className="flex-1 overflow-hidden">
        <ScenarioTemplateGallery
          onSelectTemplate={onSelectTemplate}
          selectedTemplateId={selectedTemplateId}
        />
      </div>

      <div className="flex items-center justify-end pt-4 mt-4 border-t border-gray-200">
        <button
          onClick={onNext}
          disabled={!selectedTemplateId}
          className={`px-4 py-2 rounded text-[12px] font-semibold flex items-center gap-2 transition-colors ${
            selectedTemplateId
              ? 'bg-gray-200 text-gray-800 border border-gray-300 hover:bg-gray-300'
              : 'bg-gray-50 text-gray-400 border border-gray-200 cursor-not-allowed'
          }`}
        >
          Configure Parameters
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Step 2: Parameters ───────────────────────────────────────────────────────

function StepParameters({ scenario, onChangeValue, onReset, onChangeFamily, onChangeHorizon, onBack, onNext }) {
  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-[15px] font-semibold text-gray-900 mb-1">Configure Parameters</h3>
        <p className="text-[12px] text-gray-500">
          Adjust macro, carbon, physical, transition and financial parameters. The cyan line on each slider shows the NGFS baseline.
        </p>
      </div>

      <div className="flex-1 overflow-hidden">
        <ParameterConfigurator
          scenario={scenario}
          onChangeValue={onChangeValue}
          onReset={onReset}
          onChangeFamily={onChangeFamily}
          onChangeHorizon={onChangeHorizon}
        />
      </div>

      <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-200">
        <button onClick={onBack} className="text-[12px] text-gray-500 hover:text-gray-700 flex items-center gap-1 transition-colors">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <button onClick={onNext} className="px-4 py-2 rounded text-[12px] font-semibold flex items-center gap-2 bg-gray-200 text-gray-800 border border-gray-300 hover:bg-gray-300 transition-colors">
          Edit Trajectories
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Step 3: Trajectory ───────────────────────────────────────────────────────

function StepTrajectory({ scenario, onUpdatePoint, onResetTrajectory, onBack, onNext }) {
  const [activeParam, setActiveParam] = useState(scenario.parameters[0]?.id || null);
  const paramGroups = Object.groupBy
    ? Object.groupBy(scenario.parameters, p => p.groupLabel)
    : scenario.parameters.reduce((acc, p) => {
        if (!acc[p.groupLabel]) acc[p.groupLabel] = [];
        acc[p.groupLabel].push(p);
        return acc;
      }, {});

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-[15px] font-semibold text-gray-900 mb-1">Edit Trajectories</h3>
        <p className="text-[12px] text-gray-500">
          Click any data point on the chart to edit it directly. Dashed lines show NGFS reference trajectories.
        </p>
      </div>

      <div className="flex gap-4 flex-1 overflow-hidden">
        {/* Parameter selector */}
        <div className="w-44 overflow-y-auto shrink-0 space-y-2">
          {Object.entries(paramGroups).map(([groupLabel, params]) => (
            <div key={groupLabel}>
              <p className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider px-1 mb-1">{groupLabel}</p>
              {params.map(p => {
                const hasEdits = (p.trajectory || []).some(pt => pt.isEdited);
                return (
                  <button
                    key={p.id}
                    onClick={() => setActiveParam(p.id)}
                    className={`w-full text-left text-[11px] px-2 py-1.5 rounded border transition-colors ${
                      activeParam === p.id
                        ? 'border-gray-400 bg-gray-100 text-gray-800'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span className="truncate block">{p.label}</span>
                    {hasEdits && <span className="text-[8px] text-amber-400/70">· modified</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {/* Chart area */}
        <div className="flex-1 overflow-auto">
          {activeParam && (
            <TrajectoryVisualizer
              scenario={scenario}
              paramId={activeParam}
              onUpdatePoint={onUpdatePoint}
              onResetTrajectory={onResetTrajectory}
            />
          )}
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-200">
        <button onClick={onBack} className="text-[12px] text-gray-500 hover:text-gray-700 flex items-center gap-1 transition-colors">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <button onClick={onNext} className="px-4 py-2 rounded text-[12px] font-semibold flex items-center gap-2 bg-gray-200 text-gray-800 border border-gray-300 hover:bg-gray-300 transition-colors">
          Preview Impact
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Step 4: Preview ─────────────────────────────────────────────────────────

function StepPreview({ scenario, onBack, onNext }) {
  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-[15px] font-semibold text-gray-900 mb-1">Impact Preview</h3>
        <p className="text-[12px] text-gray-500">
          Quick Monte Carlo estimate (~200 draws) showing how your scenario affects a representative 6-asset portfolio vs the NGFS Orderly baseline.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <ScenarioImpactPreviewPanel scenario={scenario} />
      </div>

      <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-200">
        <button onClick={onBack} className="text-[12px] text-gray-500 hover:text-gray-700 flex items-center gap-1 transition-colors">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <button onClick={onNext} className="px-4 py-2 rounded text-[12px] font-semibold flex items-center gap-2 bg-gray-200 text-gray-800 border border-gray-300 hover:bg-gray-300 transition-colors">
          Review & Publish
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Step 5: Review ───────────────────────────────────────────────────────────

function StepReview({ scenario, setName, setDescription, setTags, saving, onSaveDraft, onPublish, onBack }) {
  const [tagInput, setTagInput] = useState('');
  const familyMeta = NGFS_FAMILY_META[scenario.ngfsFamily] || {};
  const modifiedParams = scenario.parameters.filter(p => {
    const tgt = p.trajectories?.[scenario.ngfsFamily]?.[scenario.timeHorizon] ?? p.baseline;
    return Math.abs(p.value - tgt) > 0.001;
  });

  const handleAddTag = (e) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      setTags([...new Set([...scenario.tags, tagInput.trim()])]);
      setTagInput('');
    }
  };
  const removeTag = (t) => setTags(scenario.tags.filter(x => x !== t));

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-[15px] font-semibold text-gray-900 mb-1">Review & Publish</h3>
        <p className="text-[12px] text-gray-500">Name and describe your scenario, then save as draft or submit for approval.</p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        {/* Summary card */}
        <div className="bg-white border border-gray-200 rounded-lg p-3 flex items-start gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${familyMeta.bgClass} ${familyMeta.borderClass}`}>
            <svg className={`h-4 w-4 ${familyMeta.textClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${familyMeta.bgClass} ${familyMeta.textClass} ${familyMeta.borderClass}`}>
                {scenario.ngfsFamily}
              </span>
              <span className="text-[10px] text-gray-500">Horizon: {scenario.timeHorizon}</span>
              <span className="text-[10px] text-gray-500">{modifiedParams.length} parameter{modifiedParams.length !== 1 ? 's' : ''} customised</span>
            </div>
          </div>
        </div>

        {/* Name */}
        <div>
          <label className="block text-[11px] font-medium text-gray-500 mb-1.5">Scenario Name *</label>
          <input
            type="text"
            value={scenario.name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. High Carbon Price + Physical Risk Stress Test"
            className="w-full px-3 py-2 text-[12px] bg-gray-50 border border-black/10 rounded text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-[11px] font-medium text-gray-500 mb-1.5">Description</label>
          <textarea
            value={scenario.description}
            onChange={e => setDescription(e.target.value)}
            rows={3}
            placeholder="Describe the scenario's key assumptions, intended use, and regulatory alignment..."
            className="w-full px-3 py-2 text-[12px] bg-gray-50 border border-black/10 rounded text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>

        {/* Tags */}
        <div>
          <label className="block text-[11px] font-medium text-gray-500 mb-1.5">Tags (press Enter to add)</label>
          <div className="flex flex-wrap gap-1.5 mb-1.5">
            {scenario.tags.map(t => (
              <span key={t} className="flex items-center gap-1 text-[10px] text-gray-700 bg-gray-100 border border-gray-200 px-2 py-0.5 rounded">
                {t}
                <button onClick={() => removeTag(t)} className="text-gray-500 hover:text-gray-700">
                  <svg className="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            onKeyDown={handleAddTag}
            placeholder="Type a tag and press Enter..."
            className="w-full px-3 py-2 text-[12px] bg-gray-50 border border-black/10 rounded text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Modified params summary */}
        {modifiedParams.length > 0 && (
          <div>
            <p className="text-[11px] font-medium text-gray-500 mb-2">Customised Parameters ({modifiedParams.length})</p>
            <div className="bg-white rounded-lg p-2 space-y-1">
              {modifiedParams.slice(0, 8).map(p => {
                const baseline = p.trajectories?.[scenario.ngfsFamily]?.[scenario.timeHorizon] ?? p.baseline;
                const delta = p.value - baseline;
                const pct = baseline !== 0 ? (delta / Math.abs(baseline)) * 100 : 0;
                return (
                  <div key={p.id} className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">{p.label}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-gray-600">{p.value?.toFixed(2)} {p.unit}</span>
                      <span className={`font-semibold ${delta > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {delta > 0 ? '+' : ''}{pct.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                );
              })}
              {modifiedParams.length > 8 && (
                <p className="text-[9px] text-gray-400">+{modifiedParams.length - 8} more</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-200">
        <button onClick={onBack} className="text-[12px] text-gray-500 hover:text-gray-700 flex items-center gap-1 transition-colors">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={onSaveDraft}
            disabled={saving}
            className="px-3.5 py-2 rounded text-[12px] font-medium flex items-center gap-1.5 bg-gray-50 text-gray-600 border border-black/10 hover:bg-gray-100 transition-colors disabled:opacity-40"
          >
            {saving ? (
              <svg className="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            ) : null}
            Save Draft
          </button>
          <button
            onClick={onPublish}
            disabled={saving || !scenario.name?.trim()}
            className="px-4 py-2 rounded text-[12px] font-semibold flex items-center gap-2 bg-gray-100 text-gray-800 border border-gray-400 hover:bg-gray-300 transition-colors disabled:opacity-40"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Submit for Approval
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main wizard ──────────────────────────────────────────────────────────────

export function ScenarioBuilderWizard({ builderHook, onComplete }) {
  const [currentStep, setCurrentStep] = useState('template');

  const {
    scenario,
    saving,
    setName, setDescription, setTags,
    setNgfsFamily, setTimeHorizon,
    updateParameterValue, resetParameterValue,
    updateTrajectoryPoint, resetTrajectory,
    loadTemplate,
    saveDraft, publish,
  } = builderHook;

  const [selectedTemplateId, setSelectedTemplateId] = useState(scenario.baseTemplateId || null);

  const handleSelectTemplate = (template) => {
    setSelectedTemplateId(template.id);
    loadTemplate(template.id);
  };

  const goTo = (stepId) => setCurrentStep(stepId);
  const goNext = () => {
    const idx = STEPS.findIndex(s => s.id === currentStep);
    if (idx < STEPS.length - 1) setCurrentStep(STEPS[idx + 1].id);
  };
  const goBack = () => {
    const idx = STEPS.findIndex(s => s.id === currentStep);
    if (idx > 0) setCurrentStep(STEPS[idx - 1].id);
  };

  const handleSaveDraft = async () => {
    const res = await saveDraft();
    if (res.success && onComplete) onComplete('draft');
  };

  const handlePublish = async () => {
    const res = await publish();
    if (res.success && onComplete) onComplete('published');
  };

  return (
    <div className="flex flex-col h-full" data-testid="scenario-builder-wizard">
      <StepProgress currentStep={currentStep} onNavigate={goTo} />

      <div className="flex-1 overflow-hidden">
        {currentStep === 'template' && (
          <StepTemplate
            onSelectTemplate={handleSelectTemplate}
            selectedTemplateId={selectedTemplateId}
            onNext={goNext}
          />
        )}
        {currentStep === 'parameters' && (
          <StepParameters
            scenario={scenario}
            onChangeValue={updateParameterValue}
            onReset={resetParameterValue}
            onChangeFamily={setNgfsFamily}
            onChangeHorizon={setTimeHorizon}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {currentStep === 'trajectory' && (
          <StepTrajectory
            scenario={scenario}
            onUpdatePoint={updateTrajectoryPoint}
            onResetTrajectory={resetTrajectory}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {currentStep === 'preview' && (
          <StepPreview
            scenario={scenario}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {currentStep === 'review' && (
          <StepReview
            scenario={scenario}
            setName={setName}
            setDescription={setDescription}
            setTags={setTags}
            saving={saving}
            onSaveDraft={handleSaveDraft}
            onPublish={handlePublish}
            onBack={goBack}
          />
        )}
      </div>
    </div>
  );
}

export default ScenarioBuilderWizard;
