# Development guide

## General guidelines

The [roadmap](roadmap.md) is the single source for open tasks, priorities, and timelines. Review it before starting work or filing a pull request to avoid duplication.

Run `./bootstrap.sh` before development to install dependencies, copy `.env.example`, and execute linting/tests.

- Keep preprocessing, OCR, mapping, QC, import, and export phases decoupled.
- Prefer configuration-driven behavior and avoid hard-coded values.
- Document new processing phases with reproducible examples.

## Pair Programming with AI Agents (Encouraged)

This project promotes **collaborative development** between humans and AI agents. Agents should act as active programming partners, not just code generators:

### **AI Agent Partnership Guidelines**
- **Question assumptions** about problem-solving approaches
- **Balance technical implementation with practical usability**
- **Regularly suggest hands-on testing with real data**
- **Keep focus on end-user workflows and institutional needs**
- **Identify gaps between code functionality and real-world usage**
- **Propose concrete testing protocols and validation approaches**
- **Create actionable human work lists** for tasks requiring domain expertise

### **Practical Development Mindset**
1. **Build → Test on Real Data → Iterate** (not just build → build → build)
2. **Ask "Does this solve the actual problem?"** before adding complexity
3. **Prioritize user workflows** over technical elegance
4. **Document what humans need to do** alongside what code can do
5. **Bridge the gap** between development environment and production usage

This collaborative approach ensures technical solutions actually serve institutional and research needs.

## Testing and linting

Run the full test suite and linter before committing changes.

```bash
ruff check .
pytest
```

These checks help maintain a consistent code style and verify that new contributions do not introduce regressions.

## Release Process

This project follows semantic versioning and Keep a Changelog format for all releases.

### Creating a Release

1. **Update version numbers**:
   ```bash
   # Update version in pyproject.toml
   # Update version in CHANGELOG.md with new section
   ```

2. **Update CHANGELOG.md**:
   - Add new version section with date: `## [X.Y.Z] - YYYY-MM-DD`
   - Move items from `[Unreleased]` to the new version section
   - Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format
   - Add version comparison link at bottom of file

3. **Create and push the release**:
   ```bash
   git add .
   git commit -m "🚀 Release vX.Y.Z: Brief description"
   git tag vX.Y.Z
   git push origin main
   git push origin vX.Y.Z
   ```

4. **Update comparison links**:
   - Update `[Unreleased]` link to compare from new version
   - Add new version comparison link
   - Example format:
     ```
     [Unreleased]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/vX.Y.Z...HEAD
     [X.Y.Z]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/vX.Y.W...vX.Y.Z
     ```

### Critical Requirements

- **Always create git tags** for releases - this enables changelog comparison links
- **Use semantic versioning**: v0.1.0, v0.2.0, v1.0.0, etc.
- **Follow Keep a Changelog format** - agents must maintain this structure
- **Update pyproject.toml version** to match changelog and tag
- **Test the comparison links** - they should work on GitHub

### Changelog Format Reference

```markdown
## [Unreleased]

## [1.0.0] - 2025-01-15
### Added
- New feature descriptions

### Changed
- Modified functionality descriptions

### Fixed
- Bug fix descriptions

[Unreleased]: https://github.com/repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/repo/compare/v0.9.0...v1.0.0
```
