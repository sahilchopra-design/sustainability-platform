"""
DME NLP Pulse Score — API Routes.

Prefix: /api/v1/dme-nlp-pulse
"""
from fastapi import APIRouter
from services.dme_nlp_pulse_engine import (
    NLPPulseEngine, ProcessSignalRequest, ProcessBatchRequest, DecayRequest,
)

router = APIRouter(prefix="/api/v1/dme-nlp-pulse", tags=["DME NLP Pulse"])


@router.post("/process-signal")
def process_signal(req: ProcessSignalRequest):
    """Process a single sentiment signal through the NLP pulse pipeline."""
    return NLPPulseEngine.process_signal(req)


@router.post("/process-batch")
def process_batch(req: ProcessBatchRequest):
    """Process batch of signals and compute aggregate pulse with time decay."""
    return NLPPulseEngine.process_batch(req)


@router.post("/apply-decay")
def apply_decay(req: DecayRequest):
    """Calculate decayed signal value after elapsed time."""
    decayed = NLPPulseEngine.apply_decay(req.initial_value, req.event_type, req.elapsed_hours)
    return {
        "initial_value": req.initial_value,
        "event_type": req.event_type.value,
        "elapsed_hours": req.elapsed_hours,
        "decayed_value": round(decayed, 4),
        "decay_lambda": round(NLPPulseEngine.decay_lambda(req.event_type), 6),
    }


@router.get("/ref/event-types")
def get_event_types():
    """Reference: event types and their decay half-lives."""
    ref = NLPPulseEngine.get_reference_data()
    return ref["event_types"]


@router.get("/ref/source-tiers")
def get_source_tiers():
    """Reference: source credibility tiers."""
    ref = NLPPulseEngine.get_reference_data()
    return ref["source_tiers"]
