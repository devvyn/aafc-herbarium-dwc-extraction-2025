# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) and discovered patterns from the AAFC Herbarium DWC Extraction project.

## What are ADRs?

ADRs document important architectural and technical decisions made during the project, including:
- **Context:** Why the decision was needed
- **Decision:** What choice was made
- **Consequences:** Positive and negative impacts

## What are Pattern Records?

Pattern records document reusable solutions to common problems, suitable for application across projects:
- **Problem:** What challenge is being solved
- **Solution:** How to solve it
- **Context:** When to apply it
- **Results:** Proven outcomes

## Index

### Patterns

- [001 - Documentation Quality Gates](./001-documentation-quality-gates.md) - Shift-left validation pattern for docs-as-code (Oct 2025)
  - **Problem:** Broken links deployed to production
  - **Solution:** Pre-commit validation hooks
  - **Status:** Production-validated
  - **Applicability:** Any static site generator (MkDocs, Sphinx, Docusaurus, Hugo)

## Format

Each record follows a consistent structure:
1. Title and metadata
2. Problem statement
3. Context and forces
4. Decision/solution
5. Consequences and results
6. References and research

## Contributing

When adding new ADRs:
1. Use sequential numbering (002, 003, etc.)
2. Use descriptive filenames (`NNN-brief-description.md`)
3. Follow the established template
4. Update this README index
5. Link to related ADRs where applicable

## Related Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [ADR Tools](https://github.com/npryce/adr-tools)
- [Write the Docs](https://www.writethedocs.org/)
