# Weekend Side Projects Registry

**Purpose**: Track experimental work that may benefit collective interests without blocking primary development.

**Branch**: `experimental/weekend-projects`
**Schedule**: Weekends only (no conflict with Mon-Fri AAFC work)

## Active Projects

### 1. TUI Review Interface Enhancement
**Status**: ✅ Complete 2025-10-12
**Goal**: Terminal-friendly review interface for tmux workflows
**Benefits**:
- Accessibility for keyboard-only workflows
- Can be extracted as standalone tool
- Pattern for other terminal UIs

**Files**: `scripts/review_tui.py`

### 2. Gamification MVP - Vertical Growth Visualization
**Status**: 🚀 Started 2025-10-12 (Thanksgiving Weekend)
**Goal**: Prototype vertical growth + spaced repetition concepts
**Phase**: Weekend Experiment
**Timeline**: Sunday-Monday (no conflict with Tuesday production work)

**What we're prototyping**:
- Vertical growth meter in TUI (dataset quality ascending)
- Basic stats tracking (reviews, accuracy, points)
- Learning progress display (family expertise)
- Growth milestones visualization (🌰 → 🌱 → 🌿 → 🌳 → ✨)

**Success criteria**:
- Visualizes "approaching perfection" metaphor
- Shows both dataset growth + personal mastery
- Fun to use for 10+ specimen reviews
- Easy to revert if experiment doesn't work

**Files**:
- `scripts/review_tui_gamified.py` (new experimental version)
- `src/gamification/` (if we extract patterns)

## Potential Weekend Projects

### 2. Pattern Extraction Library
**Idea**: Extract proven patterns from this project into reusable library
**Benefits**:
- Multi-modal accessibility patterns
- API versioning strategies
- Review system architecture
- Could help other biodiversity informatics projects

### 3. Open Source Components
**Idea**: Split out reusable components (accessibility module, review engine)
**Benefits**:
- Help other herbarium/museum projects
- Get feedback from community
- Contribute to collective knowledge

### 4. Documentation Improvements
**Idea**: Write "how we built this" guides
**Benefits**:
- Help future projects learn from this
- Document decision-making process
- Share accessibility-first approach

### 5. Testing Infrastructure
**Idea**: Enhanced testing tools, snapshot testing, visual regression
**Benefits**:
- Improve code quality
- Experiment with new testing approaches
- Patterns applicable to weekday work

## Contribution Guidelines

### From Weekend → Weekday Work
1. Create feature branch from `experimental/weekend-projects`
2. Cherry-pick specific commits
3. Test thoroughly in production context
4. Submit as regular PR to `feature/v2-accessibility-first`

### From Weekday → Open Source
1. Identify reusable patterns
2. Extract to standalone module
3. Add permissive license (if appropriate)
4. Share with biodiversity informatics community

## Success Criteria

**Weekend work should**:
- ✅ Not block Monday morning progress
- ✅ Be reversible (easy to discard if not useful)
- ✅ Potentially benefit collective interests
- ✅ Be fun and educational

**Weekend work should NOT**:
- ❌ Break production systems
- ❌ Create technical debt for weekday work
- ❌ Require immediate weekday follow-up
- ❌ Compromise employment obligations

## Knowledge Sharing

Learnings from weekend work are documented here and can flow to:
- AAFC herbarium project (with proper attribution)
- Open source community
- Knowledge base patterns
- Future projects

## Time Boxing

**Weekend time limit**: 4-8 hours per weekend max
**Review frequency**: Monthly review of active projects
**Cleanup**: Quarterly cleanup of stale experiments

---

**Last Updated**: 2025-10-12
**Next Review**: 2025-11-12
