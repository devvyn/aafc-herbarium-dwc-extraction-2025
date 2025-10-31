# NiceGUI Review Interface (Experimental - Deferred)

**Status**: Archived - Filter bug blocking production use
**Date Archived**: 2025-10-31
**Reason**: NiceGUI filter UI has reactive state management bug

## Overview

Alternative Python-native review interface using NiceGUI framework. Intended to replace the Quart web app with a simpler, JavaScript-free solution.

## Why Archived

### Critical Bug: Filter UI Disappears

**Symptom**: After interacting with dropdown filters, the entire filter UI disappears from the page.

**Impact**: Cannot use for production review workflow.

**Root Cause**: NiceGUI reactive framework state management with dynamically rendered filter controls. When dropdown state changes, the parent container gets re-rendered incorrectly.

**Diagnostic Tool**: `test_filter_bug.py` - Selenium-based reproduction script

## Files Archived

1. **nicegui_app.py** (30KB)
   - Complete NiceGUI review interface implementation
   - Zone visualization system
   - Image rotation caching
   - GBIF validation integration

2. **launch_review_ui.py** (2.8KB)
   - CLI launcher for NiceGUI server
   - Configuration management

3. **test_filter_bug.py** (5.5KB)
   - Selenium test reproducing filter disappearance
   - Automated bug reproduction for future debugging

## Alternative Solution

The **Quart web app** (`src/review/web_app.py`) is stable and production-ready:
- Orthogonal filters working correctly
- No JavaScript state bugs
- Proven reliability
- Full feature parity with NiceGUI design

## Future Considerations

### If Revisiting NiceGUI

1. **Debug reactive framework**: Understand NiceGUI's state management model
2. **Simplify filters**: Use static rendering instead of dynamic updates
3. **Test incrementally**: Add one filter group at a time
4. **Evaluate complexity**: Consider if Python-native UI is worth the debugging effort

### If Abandoning NiceGUI

1. **Remove from dependencies**: Delete `nicegui>=3.2.0` from pyproject.toml
2. **Remove CLI command**: Delete `review_ui` command from cli.py
3. **Update docs**: Document Quart as the canonical review interface

## Related Changes

- **CLI integration**: cli.py has unstaged `review_ui` command (not committed)
- **Dependencies**: pyproject.toml + uv.lock have nicegui (not committed)
- **Spatial zones**: `src/spatial/` module was built for NiceGUI visualization

## Decision Point

**Recommendation**: Abandon NiceGUI approach. The Quart web app works well, and the complexity of debugging NiceGUI reactive bugs outweighs the benefit of a Python-native UI.

---

*This code represents ~40 hours of development. Archived rather than deleted to preserve implementation patterns and design decisions for future reference.*
