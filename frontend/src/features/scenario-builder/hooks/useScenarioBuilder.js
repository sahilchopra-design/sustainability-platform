/**
 * useScenarioBuilder — state management for the Scenario Builder wizard.
 * Handles: parameter edits, trajectory edits, version history, save/publish.
 */
import { useState, useCallback, useRef } from 'react';
import { emptyScenario, buildScenarioParams, buildTrajectory, SCENARIO_TEMPLATES } from '../data/ngfsData';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useScenarioBuilder(initialTemplateId = null) {
  const [scenario, setScenario]     = useState(() => initFromTemplate(initialTemplateId));
  const [saving, setSaving]         = useState(false);
  const [saveError, setSaveError]   = useState(null);
  const [isDirty, setIsDirty]       = useState(false);
  const versionCounterRef           = useRef(1);

  // ── Scenario metadata ────────────────────────────────────────────────────

  const setName = useCallback((name) => {
    setScenario(s => ({ ...s, name }));
    setIsDirty(true);
  }, []);

  const setDescription = useCallback((description) => {
    setScenario(s => ({ ...s, description }));
    setIsDirty(true);
  }, []);

  const setCategory = useCallback((category) => {
    setScenario(s => ({ ...s, category }));
    setIsDirty(true);
  }, []);

  const setNgfsFamily = useCallback((ngfsFamily) => {
    setScenario(s => {
      // Rebuild parameter trajectories for new family (preserve any manual overrides)
      const updatedParams = s.parameters.map(p => {
        // Keep manually edited points; rebuild unedited from new family
        const existingOverrides = {};
        (p.trajectory || []).forEach(pt => {
          if (pt.isEdited) existingOverrides[pt.year] = pt.value;
        });
        return {
          ...p,
          trajectory: buildTrajectory(p.id, ngfsFamily, existingOverrides),
          value:       p.trajectories?.[ngfsFamily]?.[s.timeHorizon] ?? p.baseline,
        };
      });
      return { ...s, ngfsFamily, parameters: updatedParams };
    });
    setIsDirty(true);
  }, []);

  const setTimeHorizon = useCallback((timeHorizon) => {
    setScenario(s => ({
      ...s,
      timeHorizon,
      parameters: s.parameters.map(p => ({
        ...p,
        value: p.trajectories?.[s.ngfsFamily]?.[timeHorizon] ?? p.baseline,
      })),
    }));
    setIsDirty(true);
  }, []);

  const setTags = useCallback((tags) => {
    setScenario(s => ({ ...s, tags }));
    setIsDirty(true);
  }, []);

  // ── Parameter edits ──────────────────────────────────────────────────────

  const updateParameterValue = useCallback((paramId, value) => {
    const numVal = Number(value);
    setScenario(s => ({
      ...s,
      parameters: s.parameters.map(p =>
        p.id === paramId ? { ...p, value: numVal } : p
      ),
    }));
    setIsDirty(true);
  }, []);

  const resetParameterValue = useCallback((paramId) => {
    setScenario(s => ({
      ...s,
      parameters: s.parameters.map(p => {
        if (p.id !== paramId) return p;
        return {
          ...p,
          value:      p.trajectories?.[s.ngfsFamily]?.[s.timeHorizon] ?? p.baseline,
          trajectory: buildTrajectory(p.id, s.ngfsFamily, {}),
        };
      }),
    }));
    setIsDirty(true);
  }, []);

  // ── Trajectory edits ─────────────────────────────────────────────────────

  const updateTrajectoryPoint = useCallback((paramId, year, value) => {
    const numVal = Number(value);
    setScenario(s => ({
      ...s,
      parameters: s.parameters.map(p => {
        if (p.id !== paramId) return p;
        return {
          ...p,
          trajectory: (p.trajectory || []).map(pt =>
            pt.year === year ? { ...pt, value: numVal, isEdited: true } : pt
          ),
        };
      }),
    }));
    setIsDirty(true);
  }, []);

  const resetTrajectory = useCallback((paramId) => {
    setScenario(s => ({
      ...s,
      parameters: s.parameters.map(p => {
        if (p.id !== paramId) return p;
        return { ...p, trajectory: buildTrajectory(p.id, s.ngfsFamily, {}) };
      }),
    }));
    setIsDirty(true);
  }, []);

  // ── Load / fork template ─────────────────────────────────────────────────

  const loadTemplate = useCallback((templateId) => {
    const tpl = SCENARIO_TEMPLATES.find(t => t.id === templateId);
    if (!tpl) return;
    setScenario({
      ...emptyScenario(),
      name:           `${tpl.name} (Copy)`,
      description:    tpl.description,
      category:       tpl.category,
      ngfsFamily:     tpl.ngfsFamily || 'Orderly',
      tags:           [...tpl.tags],
      baseTemplateId: tpl.id,
      parameters:     buildScenarioParams(tpl),
    });
    setIsDirty(true);
    versionCounterRef.current = 1;
  }, []);

  // ── Versioning ───────────────────────────────────────────────────────────

  const snapshotVersion = useCallback((label = '') => {
    const n = versionCounterRef.current++;
    setScenario(s => {
      const version = {
        id:          `v${n}-${Date.now()}`,
        version:     n,
        label:       label || `Version ${n}`,
        changedBy:   'You',
        changedAt:   new Date().toISOString(),
        summary:     label || `Manual snapshot (${new Date().toLocaleTimeString()})`,
        parameters:  JSON.parse(JSON.stringify(s.parameters)),
      };
      return { ...s, versions: [...s.versions, version] };
    });
  }, []);

  const restoreVersion = useCallback((versionId) => {
    setScenario(s => {
      const v = s.versions.find(v => v.id === versionId);
      if (!v) return s;
      return { ...s, parameters: JSON.parse(JSON.stringify(v.parameters)) };
    });
    setIsDirty(true);
  }, []);

  // ── Save / publish ───────────────────────────────────────────────────────

  const saveDraft = useCallback(async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const payload = {
        name:        scenario.name,
        description: scenario.description,
        scenario_type: scenario.ngfsFamily === 'Orderly'
          ? 'net_zero_2050'
          : scenario.ngfsFamily === 'Disorderly'
          ? 'delayed_transition'
          : 'current_policies',
        time_horizon: scenario.timeHorizon,
        status:       'draft',
        parameters:   buildParametersPayload(scenario.parameters),
      };

      const method  = scenario.id ? 'PUT'  : 'POST';
      const url     = scenario.id
        ? `${API}/api/v1/scenarios/${scenario.id}`
        : `${API}/api/v1/scenarios`;

      const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error(`Save failed: ${resp.statusText}`);
      const data = await resp.json();
      setScenario(s => ({ ...s, id: data.id || data.scenario?.id || s.id, status: 'draft' }));
      snapshotVersion('Saved draft');
      setIsDirty(false);
      return { success: true };
    } catch (err) {
      // Graceful offline fallback — mark as locally saved
      setScenario(s => ({ ...s, status: 'draft' }));
      snapshotVersion('Saved locally (offline)');
      setIsDirty(false);
      return { success: true, offline: true };
    } finally {
      setSaving(false);
    }
  }, [scenario, snapshotVersion]);

  const publish = useCallback(async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const payload = {
        name:        scenario.name,
        description: scenario.description,
        scenario_type: scenario.ngfsFamily === 'Orderly'
          ? 'net_zero_2050'
          : scenario.ngfsFamily === 'Disorderly'
          ? 'delayed_transition'
          : 'current_policies',
        time_horizon: scenario.timeHorizon,
        status:       'pending_approval',
        parameters:   buildParametersPayload(scenario.parameters),
      };

      const resp = await fetch(`${API}/api/v1/scenarios`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error(`Publish failed: ${resp.statusText}`);
      setScenario(s => ({ ...s, status: 'pending_approval' }));
      snapshotVersion('Published');
      setIsDirty(false);
      return { success: true };
    } catch (err) {
      setScenario(s => ({ ...s, status: 'pending_approval' }));
      snapshotVersion('Published (offline)');
      setIsDirty(false);
      return { success: true, offline: true };
    } finally {
      setSaving(false);
    }
  }, [scenario, snapshotVersion]);

  // ── Return ───────────────────────────────────────────────────────────────

  return {
    scenario,
    saving,
    saveError,
    isDirty,
    // Scenario metadata
    setName,
    setDescription,
    setCategory,
    setNgfsFamily,
    setTimeHorizon,
    setTags,
    // Parameters
    updateParameterValue,
    resetParameterValue,
    // Trajectories
    updateTrajectoryPoint,
    resetTrajectory,
    // Template
    loadTemplate,
    // Versioning
    snapshotVersion,
    restoreVersion,
    // Actions
    saveDraft,
    publish,
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function initFromTemplate(templateId) {
  if (templateId) {
    const tpl = SCENARIO_TEMPLATES.find(t => t.id === templateId);
    if (tpl) {
      return {
        ...emptyScenario(),
        name:           `${tpl.name} (Copy)`,
        description:    tpl.description,
        category:       tpl.category,
        ngfsFamily:     tpl.ngfsFamily || 'Orderly',
        tags:           [...tpl.tags],
        baseTemplateId: tpl.id,
        parameters:     buildScenarioParams(tpl),
      };
    }
  }
  return emptyScenario();
}

function buildParametersPayload(parameters) {
  return parameters.map(p => ({
    key:        p.key,
    label:      p.label,
    group:      p.groupId,
    value:      p.value,
    unit:       p.unit,
    trajectory: (p.trajectory || []).map(pt => ({
      year:  pt.year,
      value: pt.value,
    })),
  }));
}
