# Documentation Snippets: Avoiding Duplication

## Include Entire Files

Instead of copying CHANGELOG.md into docs:

```markdown
<!-- Include entire changelog from root -->
--8<-- "CHANGELOG.md"
```

Result: The changelog is always up-to-date, edit once in root.

## Include Code from Source

Instead of copy-pasting code examples:

````markdown
<!-- BAD: Duplicated code that goes stale -->
```python
from src.provenance.specimen_index import SpecimenIndex

index = SpecimenIndex("specimen_index.db")
```

<!-- GOOD: Include from actual source -->
```python
--8<-- "src/provenance/specimen_index.py:15:25"
```
````

## Include Specific Sections

Include just the installation steps from README:

```markdown
--8<-- "README.md:50:100"
```

## Include Configuration Examples

Show actual config files users will use:

````markdown
```toml
--8<-- "config/config.default.toml"
```
````

## Benefits

✅ Code examples are always correct (they're the actual code!)
✅ No copy-paste errors
✅ Documentation updates automatically when code changes
✅ Single source of truth

## See Also

- [Docs Architecture](../DOCS_ARCHITECTURE.md) - Full explanation
- [pymdownx.snippets docs](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/)
