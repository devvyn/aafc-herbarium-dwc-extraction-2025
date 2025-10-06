# Agent Orchestration Framework

**Version:** 1.0
**Status:** Design Phase
**Branch:** feature/agent-orchestration

## Vision: "Consider All Means Accessible in the World"

This framework enables intelligent pipeline composition by evaluating all available extraction engines and composing optimal workflows based on constraints (budget, deadline, quality requirements).

## Core Principles

### 1. Cost-Aware Routing
Automatically select the most cost-effective approach that meets quality requirements:
- FREE first (Vision API, Tesseract, rules engine)
- PAID fallback (GPT-4o-mini, Claude, Gemini) when needed
- Hybrid strategies (free baseline + selective paid enhancement)

### 2. Quality-Based Fallback
Progressive enhancement based on confidence scores:
- Extract with free engine
- Validate confidence levels
- Re-extract low-confidence fields with paid engines
- Ensemble voting for critical fields

### 3. Pipeline Composition
Dynamic assembly of multi-stage workflows:
- Vision API → Rules → Validation
- GPT direct extraction
- Vision + GPT hybrid (9 additional fields)
- Multi-engine ensemble with consensus voting

### 4. Meta-Project Integration
Coordination with devvyn-meta-project bridge:
- Status reporting
- Lessons learned propagation
- Cross-project pattern sharing
- Agent handoff protocols

## Architecture

```
┌──────────────────────────────────────────────┐
│  Pipeline Composer Agent                     │
│  - Evaluates constraints (budget/time/quality)│
│  - Inventories available engines             │
│  - Composes optimal pipeline                 │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Cost/Quality Decision Matrix                │
│  - Engine capabilities                       │
│  - Pricing models                            │
│  - Quality benchmarks                        │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Execution Layer                             │
│  - Plugin registry (existing)                │
│  - Multi-engine dispatch                     │
│  - Result aggregation                        │
└──────────────────────────────────────────────┘
```

## Decision Logic Example

```python
def compose_pipeline(budget: float, deadline: str, quality: str) -> List[str]:
    """
    Compose optimal extraction pipeline based on constraints.

    Args:
        budget: Available budget in USD (0 = free only)
        deadline: "immediate" | "overnight" | "flexible"
        quality: "baseline" | "high" | "research-grade"

    Returns:
        List of pipeline steps to execute
    """
    if budget == 0:
        # FREE only path
        if quality == "baseline":
            return ["vision", "rules"]
        else:
            # Use overnight free tier for better quality
            return ["gpt_free_tier", "rules_fallback"]

    if budget >= 1.60 and quality == "high":
        # Full GPT extraction (16 fields)
        return ["gpt_direct"]

    if quality == "research-grade":
        # Ensemble for maximum accuracy
        return ["vision", "gpt", "claude", "ensemble_vote"]

    # Hybrid approach: free baseline + selective enhancement
    return ["vision", "validate_confidence", "gpt_if_needed"]
```

## Components

### 1. Pipeline Composer (`agents/pipeline_composer.py`)
- Constraint evaluation
- Engine inventory
- Pipeline assembly
- Cost optimization

### 2. Engine Registry Enhancement (`engines/__init__.py`)
- Add capability metadata (fields extracted, cost per specimen, quality benchmarks)
- Enable multi-engine queries
- Support ensemble voting

### 3. Validation Agent (`agents/validator.py`)
- Confidence threshold checking
- Ground truth comparison
- Trigger selective re-extraction

### 4. Meta-Project Bridge (`agents/bridge.py`)
- Status updates to ~/devvyn-meta-project/status/
- Pattern documentation
- Handoff protocols

## Implementation Plan

### Phase 1: Core Framework (Week 1)
- [x] Design specification
- [ ] Pipeline composer implementation
- [ ] Engine capability metadata
- [ ] Decision matrix implementation

### Phase 2: Advanced Features (Week 2)
- [ ] Progressive enhancement logic
- [ ] Ensemble voting system
- [ ] Confidence-based routing
- [ ] Meta-project integration

### Phase 3: Production Hardening (Week 3)
- [ ] Error recovery
- [ ] Performance optimization
- [ ] Quality monitoring
- [ ] Documentation

## Engine Capability Matrix

| Engine | Cost/Specimen | Fields | Quality | Speed | Notes |
|--------|---------------|--------|---------|-------|-------|
| Vision API | $0 | 7 | Low-Med | Fast | FREE, handwriting struggles |
| GPT-4o-mini | $0.0006 | 16 | High | Med | Layout-aware, batch available |
| GPT-4o | $0.0030 | 16 | Very High | Med | Premium option |
| Claude Sonnet | $0.0030 | 16 | Very High | Med | Strong reasoning |
| Tesseract | $0 | 0 (text) | Low | Fast | FREE OCR fallback |
| Rules Engine | $0 | 7 | Med | Fast | Text→DWC mapping |

## Cost Scenarios

### Scenario 1: Zero Budget
**Pipeline:** Vision API → Rules Engine
**Cost:** $0
**Time:** 1-2 hours
**Quality:** Baseline (7 fields, ~5% scientificName)

### Scenario 2: Minimal Budget ($1.60)
**Pipeline:** GPT-4o-mini direct
**Cost:** $1.60
**Time:** 1-2 hours (paid) or 15-20 hours (free tier)
**Quality:** High (16 fields, layout-aware)

### Scenario 3: Research Grade ($8.65)
**Pipeline:** Vision + GPT + Claude → Ensemble Vote
**Cost:** $0 + $1.60 + $7.05 = $8.65
**Time:** 2-3 hours
**Quality:** Maximum (consensus voting, multi-model validation)

### Scenario 4: Progressive Enhancement ($0.06 - $1.60)
**Pipeline:** Vision → Validate → GPT if confidence < 0.7
**Cost:** $0 + ($0.0006 × low-confidence specimens)
**Time:** 2-3 hours
**Quality:** Optimized (free baseline, paid refinement)

## Integration with Existing Codebase

### Existing Plugin System
The current `engines/__init__.py` registry is **perfectly compatible** with agent orchestration:
- Additive-only registration (zero conflicts)
- Dynamic dispatch
- Config override pattern

### Configuration Strategy
Agent decisions can be encoded in TOML configs for reproducibility:

```toml
# config/config.agent_composed.toml
[agent]
budget = 1.60
deadline = "overnight"
quality = "high"

[pipeline]
# Computed by agent at runtime
steps = ["gpt_direct"]  # or dynamically determined

[gpt]
model = "gpt-4o-mini"
batch_mode = true  # 50% discount
```

## Meta-Project Coordination

### Bridge Messages
```json
{
  "from": "herbarium-extraction",
  "to": "meta-project",
  "type": "status_update",
  "timestamp": "2025-10-06T23:30:00Z",
  "content": {
    "branch": "feature/agent-orchestration",
    "phase": "design",
    "patterns_discovered": [
      "cost-aware routing",
      "progressive enhancement",
      "ensemble voting"
    ],
    "lessons_learned": [
      "Plugin registry enables zero-conflict parallel development",
      "Config override pattern supports branch isolation",
      "Decision logic benefits from explicit constraint evaluation"
    ]
  }
}
```

### Status Updates
Automatic reporting to `~/devvyn-meta-project/status/herbarium-extraction.json`:
- Current branch
- Pipeline composition decisions
- Quality metrics
- Cost tracking

## Success Criteria

### Technical
- ✅ Agent can compose pipelines dynamically
- ✅ Cost optimization demonstrable (achieve same quality for less)
- ✅ Quality improvement measurable (16 fields vs 7)
- ✅ Merge to main without conflicts

### Scientific
- ✅ Research-grade option available (ensemble voting)
- ✅ Baseline option remains free
- ✅ Progressive enhancement documented

### Collaboration
- ✅ Meta-project integration working
- ✅ Pattern sharing enabled
- ✅ Handoff protocols clear

---

**Next Steps:**
1. Implement pipeline composer agent
2. Add engine capability metadata
3. Create validation agent
4. Test with existing engines
5. Document decision patterns for meta-project

*Generated with Claude Code on October 6, 2025*
