# Release Process

**Version**: 1.0
**Last Updated**: 2025-10-04

## Overview

This document defines when and how to create releases for the AAFC Herbarium DWC Extraction project.

## Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH[-PRERELEASE]

Example: 1.2.3-beta.1
         │ │ │  └── Pre-release identifier (optional)
         │ │ └──── PATCH: Bug fixes, no API changes
         │ └────── MINOR: New features, backward compatible
         └──────── MAJOR: Breaking changes
```

### Version Increment Rules

**MAJOR** (1.0.0 → 2.0.0)
- Breaking changes to public API or CLI interface
- Removal of deprecated features
- Major architectural rewrites requiring migration
- Example: Remove `--old-flag` CLI option, change config format

**MINOR** (1.0.0 → 1.1.0)
- New features (backward compatible)
- New optional CLI flags or config options
- New OCR engines, storage backends, export formats
- Architectural additions (like storage abstraction) that don't break existing usage
- Example: Add S3 storage support while keeping local filesystem working

**PATCH** (1.0.0 → 1.0.1)
- Bug fixes
- Documentation updates
- Performance improvements (no API changes)
- Security patches
- Example: Fix OCR confidence calculation bug

### Pre-release Identifiers

Used for releases not yet ready for production:

- **alpha.N** - Early development, incomplete features, expect breaking changes
  - Example: `1.0.0-alpha.1` - First alpha with basic OCR working
  - Use for: Initial implementations, experimental features

- **beta.N** - Feature complete, but needs testing and may have bugs
  - Example: `1.0.0-beta.1` - All features done, testing in progress
  - Use for: Feature-complete builds ready for broader testing

- **rc.N** - Release candidate, production-ready pending final validation
  - Example: `1.0.0-rc.1` - Final checks before 1.0.0 release
  - Use for: Final verification before stable release

## When to Create a Release

### Always Tag These

✅ **Production deployments** - Any version deployed to production
✅ **Major milestones** - First working pipeline, first GBIF submission, etc.
✅ **Breaking changes** - MAJOR version bumps (config changes, CLI changes)
✅ **GitHub releases** - When creating GitHub release with assets
✅ **Public distribution** - When sharing with external users/institutions

### Consider Tagging These

🤔 **Significant features** - Storage abstraction, new OCR engines, export formats
🤔 **Architecture changes** - Even if backward compatible (helps track evolution)
🤔 **Beta/RC builds** - Testing versions before stable release
🤔 **Documentation milestones** - Complete API docs, comprehensive guides

### Don't Tag These

❌ **Work in progress** - Incomplete features, experimental branches
❌ **Internal refactors** - Code cleanup with no user-visible changes
❌ **Documentation fixes** - Typo corrections, formatting updates
❌ **Build/CI changes** - GitHub Actions updates, dependency bumps
❌ **Daily development** - Regular commits during feature development

## Release Process

### 1. Pre-Release Checklist

Before creating any release:

- [ ] All tests passing (`uv run pytest`)
- [ ] Code linting clean (`uv run ruff check .`)
- [ ] CHANGELOG.md updated with changes
- [ ] Documentation reflects new features
- [ ] Version number decided (MAJOR.MINOR.PATCH)
- [ ] Pre-release identifier chosen (if applicable)

### 2. Update CHANGELOG.md

Move changes from `[Unreleased]` to new version section:

```markdown
## [Unreleased]

(Keep this section for future changes)

## [1.0.0-beta.2] - 2025-10-04

### Added - Storage Abstraction Layer
- 🏗️ **Storage Backend Architecture** — Pluggable storage layer
  - ImageLocator protocol for storage-agnostic access
  - LocalFilesystemLocator, S3ImageLocator implementations
  - CachingImageLocator decorator for transparent caching
  - Configuration-driven backend selection

(... detailed changes ...)

[1.0.0-beta.2]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v1.0.0-beta.1...v1.0.0-beta.2
```

### 3. Commit CHANGELOG Update

```bash
git add CHANGELOG.md
git commit -m "📝 Update CHANGELOG for v1.0.0-beta.2"
```

### 4. Create Git Tag

```bash
# Create annotated tag with release notes
git tag -a v1.0.0-beta.2 -m "Release v1.0.0-beta.2: Storage Abstraction Layer

Storage abstraction architecture enables S3, MinIO, and local filesystem
backends with transparent pass-through caching. Backward compatible -
existing local filesystem workflows unaffected.

See CHANGELOG.md for full details."

# Verify tag
git tag -n5 v1.0.0-beta.2
```

### 5. Push Tag to GitHub

```bash
# Push tag to remote
git push origin v1.0.0-beta.2

# Or push all tags
git push --tags
```

### 6. Create GitHub Release

#### Option A: Using GitHub CLI (Recommended)

```bash
# Create GitHub release from tag
gh release create v1.0.0-beta.2 \
  --title "v1.0.0-beta.2: Storage Abstraction Layer" \
  --notes-file /tmp/release-notes-v1.0.0-beta.2.md \
  --prerelease  # Omit for stable releases

# Or generate notes automatically from commits
gh release create v1.0.0-beta.2 \
  --generate-notes \
  --prerelease
```

#### Option B: Using GitHub Web UI

1. Go to: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/new
2. Select tag: `v1.0.0-beta.2`
3. Title: `v1.0.0-beta.2: Storage Abstraction Layer`
4. Description: Copy from CHANGELOG.md or use detailed release notes
5. Check "This is a pre-release" for alpha/beta/rc versions
6. Click "Publish release"

### 7. Post-Release Actions

After publishing release:

- [ ] Update project version in `pyproject.toml` (if applicable)
- [ ] Announce release (if public/external users)
- [ ] Archive release notes in `docs/releases/` (optional)
- [ ] Update dependencies in downstream projects

## Release Notes Template

For detailed release notes (GitHub releases), use this template:

```markdown
# 🚀 v1.0.0-beta.2: Storage Abstraction Layer

**Release Date**: 2025-10-04
**Status**: Pre-release (Beta)
**Breaking Changes**: None

## 🎯 Highlights

Storage abstraction layer decouples extraction pipeline from storage,
enabling S3, MinIO, local filesystem, and future backends with transparent
caching.

## ✨ Features

### Storage Backend Architecture
- **ImageLocator Protocol** - Storage-agnostic interface
- **Multiple Backends** - Local filesystem, AWS S3, MinIO support
- **Transparent Caching** - Automatic local caching for remote backends
- **Configuration-Driven** - Select backend via TOML config

## 📦 Installation

```bash
git clone https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025
cd aafc-herbarium-dwc-extraction-2025
git checkout v1.0.0-beta.2
./bootstrap.sh
```

## 🔧 Configuration

See `config/config.s3-cached.toml` for S3 with caching example.

## 📖 Documentation

- [Storage Abstraction Guide](docs/STORAGE_ABSTRACTION.md)
- [Configuration Reference](config/config.default.toml)
- [Architecture Documentation](docs/architecture/)

## 🐛 Known Issues

- S3ImageLocator requires `boto3` (install with `uv pip install boto3`)
- CLI integration deferred to future release (use legacy local filesystem)

## 🙏 Acknowledgments

Developed for Agriculture and Agri-Food Canada (AAFC) herbarium digitization.

---

**Full Changelog**: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v1.0.0-beta.1...v1.0.0-beta.2
```

## Current Release Strategy

### Development Cycle (Pre-1.0.0)

We're currently in the **1.0.0 pre-release cycle** heading toward stable 1.0.0:

```
v0.3.0 (Last stable minor)
   ↓
v1.0.0-alpha.1 (Full dataset extraction MVP)
   ↓
v1.0.0-beta.1 (Feature additions)
   ↓
v1.0.0-beta.2 (Storage abstraction) ← Proposed next release
   ↓
v1.0.0-rc.1 (Release candidate)
   ↓
v1.0.0 (Stable production release)
```

### Post-1.0.0 Strategy

After 1.0.0 stable release:

- **PATCH releases** (1.0.1, 1.0.2) - Bug fixes, weekly/monthly cadence
- **MINOR releases** (1.1.0, 1.2.0) - New features, monthly/quarterly cadence
- **MAJOR releases** (2.0.0) - Breaking changes, yearly cadence (or as needed)

## Decision Framework: Should I Create a Release?

Use this decision tree:

```
Is this a breaking change?
├─ YES → MAJOR version (e.g., 2.0.0)
│         Always tag and release
│
└─ NO → Is this a new feature?
    ├─ YES → MINOR version (e.g., 1.1.0)
    │        │
    │        ├─ Significant feature? → Tag as beta/rc first, then stable
    │        └─ Small enhancement? → Tag directly as stable
    │
    └─ NO → Is this a bug fix?
        ├─ YES → PATCH version (e.g., 1.0.1)
        │        │
        │        ├─ Critical security? → Tag immediately
        │        └─ Regular bug? → Batch with other fixes
        │
        └─ NO → Documentation/refactor only?
            └─ Usually don't tag (exception: architecture changes)
```

## Storage Abstraction Release Recommendation

**Question**: Should we tag the storage abstraction as a release?

**Answer**: **Yes, as v1.0.0-beta.2** (or v1.0.0-rc.1 if nearing stable)

**Rationale**:
- ✅ Significant architectural change
- ✅ New features (S3, MinIO, caching backends)
- ✅ Backward compatible (existing workflows unaffected)
- ✅ Well-tested (18 passing tests)
- ✅ Fully documented (architecture guide, examples)
- ✅ Production-ready foundation (even if CLI integration deferred)

**Version Choice**:
- **v1.0.0-beta.2** if still testing features before 1.0.0
- **v1.0.0-rc.1** if this is final feature before stable 1.0.0
- **v1.1.0** if 1.0.0 already stable (but we're pre-1.0)

## Best Practices

### DO ✅

- **Tag milestones** - Major features, architecture changes, production deploys
- **Update CHANGELOG first** - Before creating tag
- **Use annotated tags** - `git tag -a` with descriptive message
- **Semantic versioning** - Follow MAJOR.MINOR.PATCH rules strictly
- **Pre-release for testing** - Use alpha/beta/rc before stable
- **Document breaking changes** - Clearly in CHANGELOG and release notes

### DON'T ❌

- **Tag every commit** - Only meaningful milestones
- **Skip CHANGELOG** - Always update before tagging
- **Use lightweight tags** - Always use annotated tags (`-a`)
- **Change version scheme** - Stick to semantic versioning
- **Release untested code** - All tests must pass
- **Forget GitHub release** - Tag + GitHub release for visibility

## Automation (Future)

Consider automating releases with:

- **Release Please** - Automated CHANGELOG and version bumps
- **GitHub Actions** - Auto-create GitHub releases on tag push
- **Conventional Commits** - Parse commit messages for version bumping

Example GitHub Action:

```yaml
name: Release
on:
  push:
    tags:
      - 'v*'
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Questions?

For questions about the release process, see:
- **Existing releases**: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases
- **CHANGELOG.md**: Full version history
- **CONTRIBUTING.md**: Development workflow
