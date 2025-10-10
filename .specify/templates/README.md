# Specification Templates

This directory contains templates for systematic specification and documentation practices. These templates implement the specification checkpoint strategy established in the retroactive analysis.

## When to Use Each Template

### 1. Quick Feature Assessment (`quick-feature-assessment.md`)
**Use for**: Every feature or change before implementation
**Purpose**: Determine if full specification is needed
**Time**: 5-10 minutes

**Decision Matrix**:
- **Effort > 3 days** OR **Cross-module scope** OR **High risk** → Full specification required
- **Moderate effort + single module + low risk** → Lightweight documentation
- **Simple changes** → Basic implementation with rationale

### 2. Architecture Decision Record (`architecture-decision-record.md`)
**Use for**: Significant architecture decisions
**Purpose**: Document design choices and rationale
**Time**: 30-60 minutes

**Triggers**:
- External dependency choices (APIs, libraries, services)
- Data format or protocol decisions
- Performance vs accuracy trade-offs
- Security or compliance approach decisions
- Technology stack changes

### 3. Performance Requirements (`performance-requirements.md`)
**Use for**: Features with performance implications
**Purpose**: Define measurable performance criteria
**Time**: 45-90 minutes

**Triggers**:
- Processing large datasets
- User-facing interfaces
- API or service integrations
- Batch processing workflows
- Scalability requirements

### 4. Configuration Schema (`configuration-schema.md`)
**Use for**: New or changed configuration options
**Purpose**: Ensure proper validation and migration
**Time**: 30-45 minutes

**Triggers**:
- New configuration sections
- Changed configuration format
- Additional configuration options
- Configuration validation needs

## Template Usage Guidelines

### Before Implementation
1. **Start with Quick Assessment** for every change
2. **Use appropriate templates** based on assessment outcome
3. **Complete templates** before beginning implementation
4. **Review with stakeholders** for complex features

### During Implementation
1. **Update templates** if scope or requirements change
2. **Reference templates** in commit messages and PRs
3. **Validate against requirements** defined in templates

### After Implementation
1. **Update templates** with actual implementation details
2. **Document lessons learned** for future reference
3. **Archive completed templates** in appropriate locations

## Integration with Development Workflow

### Git Workflow Integration
```bash
# 1. Feature assessment
cp .specify/templates/quick-feature-assessment.md .specify/current-feature-assessment.md
# Complete assessment

# 2. If full specification needed
/specify "Feature description"
/clarify
/plan
/tasks
/implement

# 3. Reference templates in commits
git commit -m "feat: implement user authentication

Ref: .specify/features/001-user-auth/spec.md
ADR: .specify/decisions/adr-001-auth-strategy.md
Performance: .specify/performance/auth-performance-reqs.md"
```

### Quality Gates
- **Code Review**: Check that appropriate templates were used
- **CI/CD**: Validate that specifications exist for significant changes
- **Documentation**: Ensure templates are updated with implementation details

## Template Evolution

### Adding New Templates
1. **Identify Gap**: What specification needs aren't covered?
2. **Create Template**: Follow existing format and structure
3. **Test Template**: Use on real features to validate usefulness
4. **Document Usage**: Add to this README with clear guidance

### Updating Existing Templates
1. **Collect Feedback**: What works well? What's missing?
2. **Analyze Usage**: How are templates being used in practice?
3. **Refine Content**: Improve clarity and completeness
4. **Version Changes**: Track template versions if significant changes

## Best Practices

### Template Completion
- **Be Specific**: Avoid vague statements and generalizations
- **Be Measurable**: Define concrete success criteria where possible
- **Be Realistic**: Set achievable targets based on constraints
- **Be Complete**: Don't skip sections even if they seem less relevant

### Template Maintenance
- **Keep Updated**: Update templates as implementation progresses
- **Archive Properly**: Store completed templates for future reference
- **Share Lessons**: Document what worked and what didn't
- **Iterate Process**: Improve templates based on experience

### Team Adoption
- **Start Small**: Begin with simple features to build familiarity
- **Train Team**: Ensure everyone understands when and how to use templates
- **Review Together**: Use templates as discussion tools in planning meetings
- **Celebrate Success**: Recognize good specification practices

## Common Mistakes to Avoid

### Under-Specification
- Skipping assessment for "simple" changes that turn complex
- Avoiding templates because they seem like overhead
- Not updating templates when scope changes

### Over-Specification
- Using complex templates for truly simple changes
- Creating specifications without clear stakeholder needs
- Analysis paralysis from excessive documentation

### Poor Maintenance
- Creating templates but not referencing them during implementation
- Not updating templates when requirements change
- Archiving templates without capturing lessons learned

## Success Metrics

### Process Adoption
- **Assessment Usage**: Quick assessments completed for all changes
- **Template Compliance**: Appropriate templates used based on assessment
- **Quality Improvement**: Reduced rework and clearer requirements

### Outcome Quality
- **Fewer Surprises**: Reduced unexpected requirements and scope changes
- **Better Communication**: Clearer understanding of decisions and trade-offs
- **Improved Maintenance**: Better documentation for future development

---

**Remember**: Templates are tools to improve development quality and team communication. They should enable better development, not create bureaucratic overhead. When in doubt, err on the side of more documentation rather than less.
