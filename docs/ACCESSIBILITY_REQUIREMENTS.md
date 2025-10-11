# Accessibility Requirements

**Last Updated**: 2025-10-11
**Status**: Active Development Priority

## Context

This project must support users with diverse sensory configurations, including:
- VoiceOver and other screen reader users
- Reduced visual acuity
- Keyboard-only navigation preferences
- Non-visual information processing

## Design Principle

**Information parity and interaction equity** - the fundamental information architecture and interaction patterns must work equally well across different sensory interfaces. Accessibility is not an add-on; it's a core design requirement.

## Current State Assessment

### ✅ What Works Well

**TUI Monitor** (`scripts/monitor_tui.py`):
- Text-based interface (screen reader friendly)
- Keyboard-driven navigation (q/r/d shortcuts)
- Structured information (stats, events, field quality)
- Terminal text representation of images (via rich-pixels)
- No mouse dependency

### ⚠️ Needs Improvement

**Web Review Interface** (`templates/review_dashboard.html`):
- ❌ Color-only status indicators (red/yellow/green badges)
- ❌ Mouse-dependent zoom/pan (no keyboard alternative)
- ❌ Missing ARIA labels and semantic HTML
- ❌ Visual-only priority indicators
- ❌ No screen reader announcements for state changes

## Required Improvements

### 1. Screen Reader Optimization (Priority: HIGH)

**Web Interface:**
- [ ] Add ARIA labels to all interactive elements
- [ ] Add ARIA live regions for dynamic content updates
- [ ] Semantic HTML structure (proper heading hierarchy)
- [ ] Text alternatives for all visual-only information
- [ ] Screen reader announcements for state changes

**Example Implementation:**
```html
<!-- Current -->
<span class="badge critical">CRITICAL</span>

<!-- Improved -->
<span class="badge critical"
      role="status"
      aria-label="Priority: Critical - requires immediate review">
  CRITICAL
</span>
```

### 2. Keyboard Navigation (Priority: HIGH)

**Full keyboard equivalents:**
- [ ] Arrow keys for queue navigation
- [ ] Tab/Shift+Tab for focus management
- [ ] Enter/Space for action buttons
- [ ] Keyboard-accessible zoom/pan:
  - `+/-` for zoom in/out
  - Arrow keys for pan
  - `0` to reset view
- [ ] Focus indicators visible and high contrast
- [ ] Skip links for main content areas

**Keyboard shortcuts must have:**
- Visible documentation (help screen)
- No conflicts with screen reader shortcuts
- Confirmation for destructive actions

### 3. Visual Alternatives (Priority: HIGH)

**Color is not the only indicator:**
- [ ] Text labels alongside color badges
- [ ] Icons + text for status (not just color)
- [ ] Pattern fills for charts (not just color coding)
- [ ] High contrast mode support

**Example:**
```
Critical Priority → 🔴 CRITICAL (immediate review required)
High Priority     → 🟡 HIGH (review soon)
Approved         → ✅ APPROVED (validated)
```

### 4. VoiceOver Testing (Priority: HIGH)

**Test with actual assistive technology:**
- [ ] Navigate full review workflow with VoiceOver
- [ ] Verify all information is announced correctly
- [ ] Ensure focus order is logical
- [ ] Test dynamic updates (new specimens, status changes)
- [ ] Verify keyboard shortcuts don't interfere

**Testing Checklist:**
- Can user navigate queue without mouse?
- Can user approve/reject specimens via keyboard?
- Are status changes announced?
- Is priority information clear?
- Can user access all specimen data?

### 5. Design Specification Template (Priority: MEDIUM)

**For all new features, document:**

```yaml
Feature: [Feature Name]

Information Architecture:
  [Data Point]:
    - Visual: [How it's displayed visually]
    - Auditory: [What screen reader should announce]
    - Textual: [aria-label or text alternative]
    - Keyboard: [How to access/interact via keyboard]
    - Structured: [Machine-readable format]

Interaction Patterns:
  [Action]:
    - Mouse: [Visual interaction]
    - Keyboard: [Keyboard shortcut/navigation]
    - Screen Reader: [How action is announced]
    - Feedback: [Multi-sensory confirmation]
```

## Implementation Priorities

### Phase 1: Critical Fixes (This Week)
1. Add ARIA labels to review interface
2. Implement keyboard navigation for all actions
3. Add text alternatives to color-only indicators
4. Test with VoiceOver

### Phase 2: Enhanced Accessibility (Next Sprint)
5. Add keyboard zoom/pan controls
6. Implement focus management
7. Add skip links
8. High contrast mode

### Phase 3: Documentation & Process (Ongoing)
9. Document keyboard shortcuts (help screen)
10. Create accessibility testing checklist
11. Add accessibility requirements to design templates
12. Regular VoiceOver testing in development workflow

## Resources

**Testing:**
- VoiceOver: Built into macOS (Cmd+F5)
- WAVE: Web accessibility evaluation tool
- axe DevTools: Browser extension for accessibility auditing

**Standards:**
- WCAG 2.1 Level AA (minimum target)
- ARIA Authoring Practices Guide
- Apple Human Interface Guidelines - Accessibility

## Success Metrics

**A feature is accessible when:**
1. All information available visually is also available non-visually
2. All interactions possible with mouse are possible with keyboard
3. Screen reader users can complete tasks independently
4. Focus order is logical and visible
5. Status changes are announced appropriately
6. No accessibility warnings in automated testing tools

## Notes

This document evolves as we learn more about user needs. Accessibility is not a checklist to complete but an ongoing practice of inclusive design.

**Key Insight**: The best interface is one where accessibility features benefit all users, not just those who "need" them. Keyboard shortcuts, clear labels, and structured information improve everyone's experience.
