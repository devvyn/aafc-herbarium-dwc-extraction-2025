# Data Node Architecture

**Vision**: Multi-property architecture connecting data, documentation, and software through a unified entity model.

## Surface Properties

### 1. Data (data.devvyn.ca)
**Purpose**: Simple, stable endpoints for dataset access
**Audience**: Stakeholders, researchers, data consumers

```
data.devvyn.ca/
├── aafc/
│   └── herbarium/
│       ├── latest/              # Continuous (bleeding-edge)
│       │   ├── occurrence.csv
│       │   ├── dwc-archive.zip
│       │   └── metadata.json
│       ├── v1.0/                # Stable releases
│       │   └── ...
│       └── index.html           # Dataset landing page
├── other-project/
│   └── ...
└── index.html                   # Data node entity root
```

### 2. Documentation (aafc.devvyn.ca)
**Purpose**: Comprehensive guides, API docs, development info
**Audience**: Developers, contributors, technical users

```
aafc.devvyn.ca/
├── getting-started/
├── api-reference/
├── guides/
└── ... (current MkDocs site)
```

### 3. Software (github.com/devvyn/...)
**Purpose**: Source code, issues, releases
**Audience**: Developers, open-source community

```
github.com/devvyn/aafc-herbarium-dwc-extraction-2025/
├── releases/                    # Versioned source releases
├── issues/                      # Bug reports, features
└── ... (repository)
```

## Data Node Entity Model

**Concept**: You (devvyn) as a data provider node connecting related projects

```
┌─────────────────────────────────────────────────────────┐
│  Data Node: devvyn                                      │
│  data.devvyn.ca                                         │
└───────────────┬─────────────────────────────────────────┘
                │
                ├── Project: AAFC Herbarium
                │   ├── Data: data.devvyn.ca/aafc/herbarium/
                │   ├── Docs: aafc.devvyn.ca/
                │   └── Code: github.com/devvyn/aafc-herbarium-*
                │
                ├── Project: [Future Project]
                │   ├── Data: data.devvyn.ca/[namespace]/
                │   ├── Docs: [project].devvyn.ca/
                │   └── Code: github.com/devvyn/[repo]
                │
                └── Profile: devvyn.ca (personal site)
```

## Linking Strategy

### From Data → Other Properties

```html
<!-- data.devvyn.ca/aafc/herbarium/index.html -->
<nav>
  <a href="https://aafc.devvyn.ca">📖 Documentation</a>
  <a href="https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025">💻 Source Code</a>
  <a href="https://devvyn.ca">👤 About Devvyn</a>
</nav>
```

### From Docs → Data

```markdown
<!-- aafc.devvyn.ca -->
## Download Data
Access the latest datasets at [data.devvyn.ca/aafc/herbarium](https://data.devvyn.ca/aafc/herbarium/)
```

### Cross-Property Breadcrumbs

```
devvyn.ca > AAFC Herbarium > [Data|Docs|Code]
```

## Implementation Phases

### Phase 1: Foundation (Now)
- [x] Set up data.devvyn.ca CNAME
- [ ] Create /aafc/herbarium/ namespace
- [ ] Move data-latest/ to /aafc/herbarium/latest/
- [ ] Create data node index
- [ ] Update continuous workflow

### Phase 2: Linking (Soon)
- [ ] Add cross-property navigation
- [ ] Consistent branding across properties
- [ ] Breadcrumb navigation
- [ ] Entity-aware sitemaps

### Phase 3: Federation (Future)
- [ ] API endpoints at api.devvyn.ca
- [ ] Unified search across properties
- [ ] ORCID/scholarly identity linking
- [ ] Data catalog with DOIs

## Benefits

### For Stakeholders
✅ **Simple**: `data.devvyn.ca/aafc/herbarium/latest/occurrence.csv`
✅ **Memorable**: Namespaced by project
✅ **Stable**: Separate from code churn

### For You (Data Provider)
✅ **Scalable**: Easy to add new projects
✅ **Professional**: Clear entity model
✅ **Flexible**: Properties can evolve independently

### For Projects
✅ **Discoverable**: Linked through data node
✅ **Organized**: Clear separation of concerns
✅ **Reusable**: Shared infrastructure

## Technical Implementation

### DNS Configuration

```
# Current
aafc.devvyn.ca      CNAME   devvyn.github.io

# Add
data.devvyn.ca      CNAME   devvyn.github.io
```

### GitHub Pages Setup

**Option A: Dedicated Data Repo**
```
devvyn/data.devvyn.ca (new repo)
  → Serves data.devvyn.ca
  → Contains only data files + indexes
  → No software code
```

**Option B: Current Repo with Path Routing**
```
devvyn/aafc-herbarium-dwc-extraction-2025
  → Serves both aafc.devvyn.ca AND data.devvyn.ca
  → gh-pages branch with routing:
    - aafc.devvyn.ca → /docs/ (MkDocs)
    - data.devvyn.ca → /data/ (static files)
```

**Recommendation**: Start with Option B (simpler), migrate to Option A when scaling.

### URL Routing

```javascript
// gh-pages/.github/workflows/route-domains.js
// Route based on incoming domain
if (window.location.hostname === 'data.devvyn.ca') {
  // Redirect to /data/ prefix if not already there
  if (!window.location.pathname.startsWith('/data/')) {
    window.location.pathname = '/data' + window.location.pathname;
  }
}
```

## Future Extensions

### API Surface (api.devvyn.ca)
```
api.devvyn.ca/aafc/herbarium/
  └── v1/
      ├── specimens/           # REST API
      ├── search/              # Full-text search
      └── stats/               # Dataset statistics
```

### Catalog Surface (catalog.devvyn.ca)
```
catalog.devvyn.ca/
  └── datasets/
      ├── aafc-herbarium
      ├── other-project
      └── ...
```

## Standards Compliance

- **Schema.org**: Dataset markup for Google Dataset Search
- **DCAT**: Data Catalog Vocabulary
- **Dublin Core**: Metadata standards
- **OpenAPI**: API documentation
- **W3C PROV**: Provenance tracking

---

**Status**: Phase 1 in progress
**Next**: Set up data.devvyn.ca CNAME and namespace structure
