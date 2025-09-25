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
