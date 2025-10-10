# ⚡ Specification Checkpoints: 30-Second Quick Start

**For immediate systematic development quality.**

## 🚀 Start Any Feature

```bash
.specify/scripts/quick-assess.sh
```

**That's it!** This creates an assessment that determines your next steps.

## 📋 Follow Assessment Outcome

### ✅ **Full Specification Required**
```bash
/specify "Your feature description"
/clarify
/plan
/tasks
/implement
```

### ✅ **Lightweight Documentation**
Include in commit message:
```bash
git commit -m "refactor: optimize query performance

Purpose: Reduce response time from 2s to 500ms
Approach: Added database index on frequently queried columns
Testing: Added performance test with 10k record benchmark
Impact: Improves user dashboard load time, no breaking changes"
```

### ✅ **Simple Implementation**
Include rationale in commit:
```bash
git commit -m "fix: correct validation error message

Rationale: User reported unclear error message
Change: Updated 'Invalid input' to 'Email format invalid'
Testing: Manual verification of error display"
```

## 🎯 Architecture Decisions

```bash
.specify/scripts/new-adr.sh "your-decision-name"
```

Creates numbered ADR with template → Complete → Reference in commits

## ✅ Commit Validation

```bash
.specify/scripts/check-commit.sh "your commit message"
```

Validates specification compliance before committing.

## 📚 Key Resources

- **Templates**: `.specify/templates/`
- **Examples**: `.specify/retro-specs/`
- **Decisions**: `.specify/decisions/`
- **Full Guide**: `.specify/ACTIVATION_GUIDE.md`

---

**Systematic quality in 30 seconds. Every feature. Every time. 🎯**
