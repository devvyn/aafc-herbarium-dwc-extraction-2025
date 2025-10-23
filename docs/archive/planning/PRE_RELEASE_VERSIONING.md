# Pre-Release Versioning Guide

**Version**: 1.0
**Last Updated**: 2025-10-04

## Overview

Pre-release identifiers (alpha, beta, rc) signal the maturity and stability of software before a stable release. This guide explains when to use each identifier and the criteria for progression.

## The Pre-Release Spectrum

```
Development → alpha → beta → rc → stable
   (private)    ↓       ↓      ↓      ↓
              Unstable  Testing  Final  Production
              Incomplete Complete Checks  Ready
```

## Alpha (α) - Early Development

### What is Alpha?

**Alpha releases** are early, incomplete implementations where:
- Features are still being developed
- APIs may change dramatically
- Breaking changes are expected
- Internal testing is ongoing
- Not all planned features are implemented

### Characteristics

**Stability**: ⚠️ Unstable - expect bugs and crashes
**API Changes**: ✋ Frequent breaking changes expected
**Features**: 🚧 Incomplete, under active development
**Testing**: 🔬 Limited internal testing
**Documentation**: 📝 May be incomplete or outdated
**Audience**: 👨‍💻 Developers and early adopters only

### When to Use Alpha

Use `alpha.N` when:
- ✅ First working prototype exists
- ✅ Core functionality partially implemented
- ✅ Breaking changes expected in next iteration
- ✅ Need feedback on approach/architecture
- ✅ Not feature-complete yet

**Example Criteria**:
- 30-60% of planned features implemented
- Major features work but missing edge cases
- Known bugs and incomplete error handling
- Documentation exists but may be inaccurate

### Alpha Progression Rules

**Increment alpha.N** (e.g., alpha.1 → alpha.2) when:
- Adding new incomplete features
- Making breaking changes to API
- Significant refactoring in progress
- Each development milestone reached

**Move to beta** when:
- All planned features implemented (even if buggy)
- API stabilized (no more breaking changes expected)
- Ready for wider testing
- Documentation reflects current state

### Example: Alpha Release Lifecycle

```
v1.0.0-alpha.1 - First working OCR pipeline
  ↓ Add Darwin Core extraction (incomplete)
v1.0.0-alpha.2 - Basic DWC extraction working
  ↓ Add GBIF validation (breaking API change)
v1.0.0-alpha.3 - GBIF integration complete
  ↓ All planned features now implemented
v1.0.0-beta.1 - Feature complete, begin testing
```

## Beta (β) - Feature Complete Testing

### What is Beta?

**Beta releases** are feature-complete implementations where:
- All planned features are implemented
- API is stabilized (no more breaking changes)
- Focus shifts to bug fixes and polish
- Ready for broader testing
- May still have known bugs

### Characteristics

**Stability**: ⚙️ Mostly stable - bugs expected but not crashes
**API Changes**: 🔒 API frozen - only bug fixes, no breaking changes
**Features**: ✅ Feature complete - all planned functionality present
**Testing**: 🧪 Extensive testing in progress
**Documentation**: 📚 Complete and accurate
**Audience**: 👥 Early adopters and testers

### When to Use Beta

Use `beta.N` when:
- ✅ All planned features implemented
- ✅ API is stable (no breaking changes planned)
- ✅ Core functionality works reliably
- ✅ Known bugs being fixed
- ✅ Documentation is complete
- ✅ Ready for user testing

**Example Criteria**:
- 90%+ of features working correctly
- No critical bugs (P0/P1 issues resolved)
- Performance is acceptable
- Security vulnerabilities addressed
- Test coverage >80%

### Beta Progression Rules

**Increment beta.N** (e.g., beta.1 → beta.2) when:
- Fixing bugs discovered during testing
- Adding minor polish/improvements (no new features)
- Improving documentation
- Performance optimizations

**Move to rc** when:
- No known critical or major bugs
- All tests passing consistently
- Documentation complete and reviewed
- Performance meets requirements
- Ready for final validation

### Example: Beta Release Lifecycle

```
v1.0.0-beta.1 - Feature complete, begin testing
  ↓ Fix 15 bugs found during testing
v1.0.0-beta.2 - Major bugs fixed, more testing
  ↓ Fix 8 more bugs, optimize performance
v1.0.0-beta.3 - Minor bugs fixed, stable
  ↓ Final testing - no new bugs found
v1.0.0-rc.1 - Release candidate
```

## RC (Release Candidate) - Final Validation

### What is RC?

**Release Candidates** are production-ready builds undergoing final validation:
- Believed to be stable enough for production
- No known critical bugs
- Only showstopper bugs will block release
- Final verification and stakeholder approval
- Next release could be stable (if no issues found)

### Characteristics

**Stability**: ✅ Production-ready - should be stable
**API Changes**: 🔒 Frozen - absolutely no changes unless critical bug
**Features**: ✅ Complete and polished
**Testing**: ✔️ Comprehensive testing complete
**Documentation**: 📖 Final, production-ready
**Audience**: 🌍 All users (production trial)

### When to Use RC

Use `rc.N` when:
- ✅ All tests passing
- ✅ No known critical or major bugs
- ✅ Performance validated
- ✅ Security audit complete (if applicable)
- ✅ Documentation finalized
- ✅ Stakeholder approval pending
- ✅ Ready for production deployment

**Example Criteria**:
- Zero known P0/P1 (critical/major) bugs
- All acceptance criteria met
- Performance benchmarks passed
- Code review complete
- Legal/compliance approved (if applicable)

### RC Progression Rules

**Increment rc.N** (e.g., rc.1 → rc.2) when:
- Critical bug discovered during RC phase
- Only showstopper issues justify new RC
- Each fix creates new RC for re-validation

**Move to stable** when:
- RC deployed to production successfully
- No critical issues found after soak period (e.g., 1-2 weeks)
- Stakeholder sign-off received
- Final approval checklist complete

### Example: RC Release Lifecycle

```
v1.0.0-rc.1 - Release candidate
  ↓ Deploy to staging, test for 1 week
  ↓ Critical bug found in edge case
v1.0.0-rc.2 - Bug fixed, re-test
  ↓ Deploy to staging, test for 1 week
  ↓ No issues found, stakeholder approval
v1.0.0 - Stable production release
```

## Decision Framework

### Maturity Assessment

Use this checklist to determine appropriate pre-release identifier:

#### Alpha Checklist
- [ ] Core features partially implemented
- [ ] API may change
- [ ] Breaking changes expected
- [ ] Known bugs and missing features
- [ ] Internal testing only

**If >3 checked → Use alpha.N**

#### Beta Checklist
- [ ] All planned features implemented
- [ ] API stabilized (no breaking changes)
- [ ] Core functionality working
- [ ] Documentation complete
- [ ] Ready for user testing

**If >4 checked → Use beta.N**

#### RC Checklist
- [ ] All features complete and polished
- [ ] No known critical bugs
- [ ] All tests passing
- [ ] Performance validated
- [ ] Stakeholder approval pending

**If all checked → Use rc.N**

#### Stable Checklist
- [ ] RC deployed successfully
- [ ] No critical issues in production
- [ ] Stakeholder sign-off received
- [ ] Soak period complete

**If all checked → Release as stable MAJOR.MINOR.PATCH**

### Quality Gates

Each progression requires passing quality gates:

```
alpha → beta: Feature Completeness Gate
  ✅ All planned features implemented
  ✅ API stabilized
  ✅ Documentation complete

beta → rc: Quality Gate
  ✅ No critical/major bugs
  ✅ All tests passing
  ✅ Performance acceptable

rc → stable: Production Gate
  ✅ Production validation successful
  ✅ No showstoppers found
  ✅ Stakeholder approval
```

## Timeline Guidelines

### Development Velocity

**Alpha Phase**: Days to weeks per increment
- Rapid iteration
- Frequent releases (daily/weekly)
- Quick feedback loops

**Beta Phase**: Weeks per increment
- Slower, more deliberate
- Weekly/biweekly releases
- Thorough testing between releases

**RC Phase**: Weeks per increment
- Careful validation
- Minimal changes
- Production-like testing

### Typical Durations

**Alpha → Beta**: 1-3 months
- Depends on feature scope
- Multiple alpha releases expected

**Beta → RC**: 2-6 weeks
- Bug fixing and polishing
- 2-4 beta releases typical

**RC → Stable**: 1-3 weeks
- Final validation
- 1-2 RC releases typical (ideally 1)

## Numbering Schemes

### Sequential Numbering (Recommended)

```
v1.0.0-alpha.1
v1.0.0-alpha.2
v1.0.0-alpha.3
v1.0.0-beta.1
v1.0.0-beta.2
v1.0.0-rc.1
v1.0.0
```

**Advantages**:
- Clear progression
- Easy to compare versions
- Standard semantic versioning

### Date-Based Numbering

```
v1.0.0-alpha.20251001
v1.0.0-alpha.20251015
v1.0.0-beta.20251101
v1.0.0-rc.20251201
v1.0.0
```

**Use when**:
- Rapid iteration (multiple per day)
- Need to track exact build date
- CI/CD automated releases

### Named Alphas (Avoid)

```
v1.0.0-alpha-storage
v1.0.0-alpha-ui
v1.0.0-beta-final
```

**Why avoid**:
- Not sortable
- Confusing progression
- Breaks semantic versioning

## Communication Guidelines

### Alpha Releases

**Announcement Template**:
```
⚠️ Alpha Release: v1.0.0-alpha.2

EXPERIMENTAL - Not for production use

What's New:
- Basic Darwin Core extraction working
- Added preliminary GBIF validation

Known Issues:
- API may change in next release
- Performance not optimized
- Missing error handling in some cases

Feedback Welcome:
Please test and report issues. This is an early preview.
```

**Warning Labels**:
- ⚠️ EXPERIMENTAL
- 🚧 UNDER DEVELOPMENT
- ⛔ NOT FOR PRODUCTION

### Beta Releases

**Announcement Template**:
```
🧪 Beta Release: v1.0.0-beta.1

FEATURE COMPLETE - Testing phase

What's New:
- All planned features implemented
- API is now stable (no breaking changes)
- Ready for user testing

Known Issues:
- Minor bugs in edge cases (see issue tracker)
- Documentation updates in progress

How to Help:
Please test your workflows and report any issues.
API is frozen - safe to build against.
```

**Warning Labels**:
- 🧪 BETA - Testing phase
- ⚠️ May contain bugs
- 👥 Feedback wanted

### RC Releases

**Announcement Template**:
```
✅ Release Candidate: v1.0.0-rc.1

PRODUCTION READY - Final validation

This release is believed to be production-ready. Unless critical
issues are found, this will become v1.0.0 stable.

Changes Since Beta:
- Fixed all known critical bugs
- Performance optimizations
- Documentation finalized

Final Testing:
Please deploy to staging and validate production workflows.
Report any critical issues immediately.
```

**Warning Labels**:
- ✅ RELEASE CANDIDATE
- 🎯 Production trial
- 📋 Final validation

## Best Practices

### DO ✅

**Version Progression**:
- ✅ Always increment pre-release identifier when making changes
- ✅ Follow alpha → beta → rc → stable progression
- ✅ Document what changed between pre-releases
- ✅ Announce pre-releases with clear warnings

**Testing**:
- ✅ Increase test rigor at each stage (alpha → beta → rc)
- ✅ Beta testing should include real users
- ✅ RC testing should simulate production

**Communication**:
- ✅ Clear labels (ALPHA, BETA, RC) in all communications
- ✅ List known issues and limitations
- ✅ Explain what feedback you're seeking

### DON'T ❌

**Version Management**:
- ❌ Skip stages (alpha → rc without beta)
- ❌ Add features during RC phase
- ❌ Release stable if RC had critical bugs
- ❌ Reuse pre-release numbers (no v1.0.0-beta.1 twice)

**Testing**:
- ❌ Skip testing phases to ship faster
- ❌ Promote to next stage without meeting criteria
- ❌ Release RC with known critical bugs

**Communication**:
- ❌ Call alpha releases "beta" (sets wrong expectations)
- ❌ Promote pre-releases without clear warnings
- ❌ Hide known issues from users

## Example: AAFC Herbarium Project

### Current State Analysis

**v1.0.0-beta.1** (Current latest tag):
- Full dataset extraction working ✅
- OCR pipeline complete ✅
- Darwin Core export functional ✅
- Some architectural improvements in progress 🚧

**Storage Abstraction (Latest commit)**:
- New architecture implemented ✅
- Backward compatible (no breaking changes) ✅
- 18 tests passing ✅
- Documentation complete ✅
- CLI integration deferred (not feature-incomplete) ✅

### Recommendation: v1.0.0-beta.2

**Why beta (not rc)?**
- ✅ Feature complete - All extraction features working
- ✅ Backward compatible - Existing workflows unaffected
- ✅ Well tested - 18 new tests passing
- ⚠️ Not quite ready for production validation
- ⚠️ More architectural work may come
- ⚠️ Need user testing of new features

**Why not rc?**
- No production deployment/validation yet
- Additional features may be added before 1.0.0
- Stakeholder validation not complete
- Soak testing not performed

**Why not alpha?**
- Not breaking changes (backward compatible)
- Feature is complete (Phase 1 done)
- API is stable (ImageLocator protocol finalized)
- Well tested and documented

### Path to v1.0.0 Stable

```
v1.0.0-beta.2 (Storage abstraction) ← Current recommendation
  ↓
v1.0.0-beta.3 (Additional features/fixes)
  ↓
v1.0.0-beta.4 (Final polish)
  ↓
v1.0.0-rc.1 (Production validation)
  ↓ Deploy to staging, 2-week soak
  ↓ AAFC stakeholder approval
  ↓ No critical issues found
v1.0.0 (Stable production release)
```

## Quick Reference Table

| Stage | Stability | Features | API | Testing | Audience | Changes Allowed |
|-------|-----------|----------|-----|---------|----------|-----------------|
| **alpha.N** | Unstable | Incomplete | Unstable | Internal | Developers | Breaking changes OK |
| **beta.N** | Mostly stable | Complete | Frozen | Extensive | Early adopters | Bug fixes only |
| **rc.N** | Production-ready | Polished | Frozen | Comprehensive | All users | Critical fixes only |
| **stable** | Production | Final | Frozen | Validated | Everyone | Patch releases only |

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Software Release Life Cycle (Wikipedia)](https://en.wikipedia.org/wiki/Software_release_life_cycle)
- [Python PEP 440 - Version Identification](https://www.python.org/dev/peps/pep-0440/)
- [Node.js Release Process](https://nodejs.org/en/about/releases/)

## Summary

**Alpha**: "It works, but things will change"
**Beta**: "All features done, but bugs remain"
**RC**: "Production ready, just verifying"
**Stable**: "Production validated, ship it"

Choose based on **feature completeness**, **stability**, and **testing maturity**, not arbitrary timelines.
