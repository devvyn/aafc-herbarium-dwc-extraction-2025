# Version History Analysis

**Version**: 1.0
**Last Updated**: 2025-10-04

## Overview

This document analyzes the existing version history of the AAFC Herbarium DWC Extraction project, explains version number jumps, and provides recommendations for clean versioning going forward.

## Executive Summary

The project's version history reflects **exploratory development** rather than strict semantic versioning adherence. Version numbers jumped non-linearly (0.1.x → 1.0.0-beta.1 → 0.2.0 → 0.3.0 → 1.0.0-alpha.1) as the team experimented with different release strategies and discovered the appropriate scope for v1.0.0.

**Key Finding**: The version "chaos" is actually **healthy exploration** that ultimately converged on the right strategy - treating v1.0.0 as "production-ready full pipeline" rather than "first release."

## Timeline of Releases

### Phase 1: Initial Development (Aug 2025)

```
v0.1.0 (2025-08-20) - Initial commit
  └── 1 commit
v0.1.1 (2025-08-21) - Project skeleton
  └── 150 commits (!)
v0.1.2 (2025-09-02) - Rapid development
  └── 7 commits
v0.1.3 (2025-09-08) - Developer docs milestone
  └── 73 commits
v0.1.4 (2025-09-09) - Continued development
  └── 65 commits
```

**Observations**:
- **Rapid initial development**: 150 commits between v0.1.1 and v0.1.2
- **PATCH version misuse**: These should have been MINOR (new features)
- **No GitHub releases**: These were git tags only, not formal releases

**What Was Built**:
- Complete OCR pipeline (Tesseract, Apple Vision, GPT)
- Darwin Core schema and mapping
- Preprocessing pipeline
- QC functions
- Web review interface
- Export/import workflows
- Comprehensive documentation

**Why PATCH versions?**: Early experimentation, learning semantic versioning

### Phase 2: The "1.0 Beta" Experiment (Sep 2025)

```
v1.0.0-beta.1 (2025-09-21) - Hybrid OCR→GPT Triage Pipeline
  └── 2 commits (!!)
v0.2.0 (2025-09-24) - Phase 1 Major Enhancements
```

**The Jump**: v0.1.4 → v1.0.0-beta.1 (skipped 0.2-0.9!)

**Why This Happened**:
- Team thought hybrid triage system was production-ready
- Believed v1.0.0 was imminent
- Tagged as beta.1 to signal "almost there"
- **GitHub Release Created**: "🚀 Beta Release 1.0.0-beta.1: Hybrid OCR→GPT Triage Pipeline"

**Features in v1.0.0-beta.1**:
- Intelligent hybrid triage (OCR vs GPT routing)
- Cost-optimized processing
- Contextual GPT for herbarium specimens
- Multilingual OCR (80+ languages)
- >95% accuracy on clear labels
- 60% cost reduction

**The Reversal**: v1.0.0-beta.1 → v0.2.0

**Why Go Backwards?**:
- Realized v1.0.0 should mean "production deployment ready"
- Hybrid triage was a significant feature, but not the **full pipeline**
- Needed more work before true v1.0.0
- v0.2.0 represented a MINOR version bump from conceptual v0.1.x baseline

**What Was in v0.2.0** (the "real" Phase 1):
- Versioned DwC-A export system
- Official schema integration (TDWG)
- Enhanced mapping system with fuzzy matching
- Enhanced GBIF integration
- Comprehensive documentation
- Expanded testing

**Note**: v0.2.0 had **no GitHub release** - only CHANGELOG entry

### Phase 3: Research Breakthrough (Sep 2025)

```
v0.3.0 (2025-09-25) - OCR Research Breakthrough
  └── 16 commits from v0.2.0
```

**Why v0.3.0?**: Major milestone deserving MINOR bump

**What Changed**:
- Comprehensive OCR engine analysis
- **Empirical finding**: Apple Vision 95% vs Tesseract 15% accuracy
- Production-ready Apple Vision integration
- Research documentation system
- Architecture shift: Apple Vision-first, retire Tesseract

**GitHub Release**: ✅ "v0.3.0: OCR Research Breakthrough - Apple Vision 95% Accuracy"

**Impact**:
- Eliminates API dependency for 95% of specimens
- $1600/1000 specimens cost savings
- Evidence-based production deployment strategy

### Phase 4: The "Alpha After Beta" Paradox (Oct 2025)

```
v0.3.0 (2025-09-25)
  └── 20 commits
v1.0.0-alpha.1 (2025-10-04) - Full Dataset Extraction Pipeline MVP
  └── Current HEAD
```

**The Paradox**: Released alpha.1 AFTER beta.1

**Why This Makes Sense**:
- v1.0.0-beta.1 was **premature** - jumped to 1.0 too early
- Team reset expectations: v1.0.0 = "production-ready **full pipeline**"
- v1.0.0-alpha.1 = "first working end-to-end on real data"
- This is the **correct** alpha milestone for v1.0.0

**What Was in v1.0.0-alpha.1**:
- Full dataset extraction (2,885 specimens processed)
- 93.7% success rate (2,702 Darwin Core records)
- GBIF-compatible CSV output
- Complete OCR database
- OCR-only config (addresses pipeline rollback bug)
- Extraction from saved OCR (`scripts/extract_dwc_from_ocr.py`)

**GitHub Release**: ✅ "🚀 v1.0.0-alpha.1: Full Dataset Extraction Pipeline MVP"

### Phase 5: Current State (Oct 2025)

```
v1.0.0-alpha.1 (2025-10-04)
  └── 11 commits (uncommitted)
[Proposed] v1.0.0-beta.2 - Storage Abstraction Layer
```

**What's Been Added Since alpha.1**:
- Storage abstraction architecture (S3, MinIO, local filesystem)
- Transparent caching with LRU eviction
- 18 passing tests
- Comprehensive documentation
- Release process guidelines
- Pre-release versioning criteria

## Version Number Jumps Explained

### Jump 1: v0.1.4 → v1.0.0-beta.1

**Reasoning**: Team believed hybrid triage made project production-ready
**Reality**: Feature-complete ≠ production-ready
**Lesson**: v1.0.0 should mean "deployed to production," not "features done"

### Jump 2: v1.0.0-beta.1 → v0.2.0

**Reasoning**: Reset to 0.x series to continue development
**Reality**: Correct decision - needed more foundational work
**Lesson**: Don't jump to 1.0 until you're certain

### Jump 3: v0.3.0 → v1.0.0-alpha.1

**Reasoning**: Fresh start on v1.0.0 journey with correct milestone
**Reality**: This is the **real** first alpha for v1.0.0
**Lesson**: Alpha comes before beta (reset the pre-release sequence)

## What Each Version Really Represents

| Version | What It Was | What It Should Have Been | GitHub Release? |
|---------|-------------|--------------------------|-----------------|
| v0.1.0 | Initial commit | ✅ Correct | ❌ No |
| v0.1.1 | Project skeleton | ✅ Correct (PATCH ok for early dev) | ❌ No |
| v0.1.2 | 150 commits of features | ❌ Should be v0.2.0 (MINOR) | ❌ No |
| v0.1.3 | Developer docs + features | ❌ Should be v0.3.0 (MINOR) | ❌ No |
| v0.1.4 | More features | ❌ Should be v0.4.0 (MINOR) | ❌ No |
| v1.0.0-beta.1 | Hybrid triage system | ❌ Should be v0.5.0-beta.1 | ✅ Yes |
| v0.2.0 | Phase 1 enhancements | ✅ Correct reset | ❌ No |
| v0.3.0 | OCR research | ✅ Correct (MINOR) | ✅ Yes |
| v1.0.0-alpha.1 | Full dataset MVP | ✅ Correct (first real 1.0 alpha) | ✅ Yes |

## Pattern Recognition

### What Worked ✅

1. **GitHub Releases for Major Milestones**: v1.0.0-beta.1, v0.3.0, v1.0.0-alpha.1
2. **MINOR Bumps for Features**: v0.2.0 → v0.3.0 (OCR research)
3. **Pre-release Identifiers**: Using alpha/beta to signal maturity
4. **Version Reset**: Recognizing v1.0.0-beta.1 was premature and resetting

### What Didn't Work ❌

1. **PATCH for Features**: v0.1.1 → v0.1.2 (150 commits!)
2. **Premature v1.0**: Jumping to 1.0.0-beta.1 too early
3. **No GitHub Releases for 0.2.0**: Significant milestone missed
4. **Alpha After Beta**: Confusing progression (should be alpha → beta)

## Lessons Learned

### 1. Define v1.0.0 Criteria Early

**Mistake**: Team wasn't aligned on what v1.0.0 meant
**Fix**: v1.0.0 = "Production-ready full pipeline deployed to AAFC"

**Criteria Established**:
- ✅ Full dataset extraction working
- ✅ Production deployment successful
- ✅ Stakeholder validation complete
- ✅ Performance meets requirements
- ✅ Documentation complete

### 2. Use MINOR for Features, PATCH for Fixes

**Mistake**: v0.1.2 had 150 commits (mostly features)
**Fix**: Feature = MINOR bump, Bug fix = PATCH bump

**Examples**:
- ✅ v0.2.0: New export system (MINOR)
- ✅ v0.3.0: New OCR engine (MINOR)
- ❌ v0.1.2: New features (should be v0.2.0)

### 3. Pre-release Progression: alpha → beta → rc

**Mistake**: Released beta.1 before alpha.1
**Fix**: Always progress alpha → beta → rc

**Correct Sequence**:
```
v1.0.0-alpha.1 (Feature incomplete)
v1.0.0-alpha.2 (More features)
v1.0.0-beta.1 (Feature complete, testing)
v1.0.0-beta.2 (Bug fixes)
v1.0.0-rc.1 (Production validation)
v1.0.0 (Stable release)
```

### 4. GitHub Release for Every Significant Milestone

**Mistake**: v0.2.0 and v0.1.x had no GitHub releases
**Fix**: Create GitHub release for every MINOR/MAJOR version

**Benefits**:
- Visibility for users
- Downloadable assets
- Release notes in one place
- Automatic notifications

## Current State Assessment

### Where We Are

**Latest Tag**: v1.0.0-alpha.1 (2025-10-04)
**Latest Commit**: Storage abstraction (11 commits ahead)
**Maturity**: Feature-complete storage abstraction, backward compatible

### What We've Built Since alpha.1

1. **Storage Abstraction Layer** (8 new modules)
   - ImageLocator protocol
   - Local filesystem, S3, MinIO backends
   - Transparent caching decorator
   - Configuration-driven factory

2. **Testing** (18 passing tests)
   - LocalFilesystemLocator: 11 tests
   - CachingImageLocator: 7 tests
   - Edge cases covered

3. **Documentation** (3 new docs)
   - Architecture guide (STORAGE_ABSTRACTION.md)
   - Release process (RELEASE_PROCESS.md)
   - Pre-release versioning (PRE_RELEASE_VERSIONING.md)

### Next Appropriate Version: v1.0.0-beta.2

**Why beta.2 (not alpha.2)?**

**Feature Completeness**: ✅
- Storage abstraction fully implemented
- All planned features working
- API stable (no breaking changes)
- Backward compatible

**Stability**: ✅
- 18 passing tests
- No known critical bugs
- Production-quality code

**Testing Maturity**: ⚠️
- Unit tested, but not production-validated
- Need user testing of new architecture
- CLI integration deferred (doesn't block beta)

**Conclusion**: Too mature for alpha, not quite ready for rc

## Recommendations Going Forward

### 1. Tag v1.0.0-beta.2 Now

**Commands**:
```bash
# Update CHANGELOG (move Unreleased to [1.0.0-beta.2])
git add CHANGELOG.md
git commit -m "📝 Update CHANGELOG for v1.0.0-beta.2"

# Create annotated tag
git tag -a v1.0.0-beta.2 -m "Release v1.0.0-beta.2: Storage Abstraction Layer

Storage abstraction architecture enables S3, MinIO, and local filesystem
backends with transparent pass-through caching. Backward compatible.

See CHANGELOG.md for full details."

# Push tag
git push origin v1.0.0-beta.2

# Create GitHub release
gh release create v1.0.0-beta.2 \
  --title "v1.0.0-beta.2: Storage Abstraction Layer" \
  --notes-file docs/release-notes/v1.0.0-beta.2.md \
  --prerelease
```

### 2. Establish Clear v1.0.0 Criteria

**v1.0.0 Stable Criteria** (must all be true):
- [ ] Full dataset extraction validated in production
- [ ] AAFC stakeholder sign-off received
- [ ] No known P0/P1 (critical/major) bugs
- [ ] Performance benchmarks met
- [ ] Security review complete (if applicable)
- [ ] Documentation complete and reviewed
- [ ] Production deployment successful (2-week soak)

### 3. Follow Strict Progression: beta → rc → stable

**Path to v1.0.0**:
```
v1.0.0-beta.2 (Storage abstraction) ← Proposed next
  ↓ Add features, fix bugs
v1.0.0-beta.3+ (Polish, additional features)
  ↓ Feature freeze, final testing
v1.0.0-rc.1 (Production validation)
  ↓ 2-week soak, stakeholder approval
  ↓ Critical bugs only (if found, → rc.2)
v1.0.0 (Stable production release)
```

**No more version jumps!**

### 4. Create GitHub Release for Every Tag

**Process**:
1. Tag in git: `git tag -a vX.Y.Z`
2. Push tag: `git push origin vX.Y.Z`
3. Create release: `gh release create vX.Y.Z --prerelease` (or omit for stable)
4. Add release notes (use template from RELEASE_PROCESS.md)

### 5. Maintain CHANGELOG Discipline

**Before Every Release**:
1. Move changes from `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`
2. Add comparison link: `[X.Y.Z]: https://github.com/.../compare/vPREV...vX.Y.Z`
3. Commit CHANGELOG update before creating tag

### 6. Version Bump Rules

**Reference Card**:
- New feature (backward compatible) → MINOR (0.1.0 → 0.2.0)
- Bug fix (no new features) → PATCH (0.1.0 → 0.1.1)
- Breaking change → MAJOR (0.9.0 → 1.0.0)
- Pre-release increment → +1 identifier (beta.1 → beta.2)

## Summary

The project's version history reflects **healthy exploration** of what v1.0.0 should mean. The team correctly realized that v1.0.0-beta.1 was premature and reset to continue development in the 0.x series (v0.2.0, v0.3.0) before starting the **correct** v1.0.0 journey with v1.0.0-alpha.1.

**Key Insights**:
1. **v1.0.0-beta.1** - Premature (great feature, wrong version)
2. **v0.2.0, v0.3.0** - Correct reset to 0.x for continued development
3. **v1.0.0-alpha.1** - Correct starting point for v1.0.0 journey
4. **v1.0.0-beta.2** - Next logical step (storage abstraction)

**Going Forward**: Strict semver adherence with clear v1.0.0 criteria

The version "chaos" was actually the team **finding the right strategy** - and they did! 🎯

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [RELEASE_PROCESS.md](./RELEASE_PROCESS.md) - How to release
- [PRE_RELEASE_VERSIONING.md](./PRE_RELEASE_VERSIONING.md) - Alpha/beta/rc criteria
- [CHANGELOG.md](../../changelog.md) - Full version history
