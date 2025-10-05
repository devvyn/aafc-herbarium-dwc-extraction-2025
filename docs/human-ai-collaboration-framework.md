# Human-AI Collaboration Framework for Scientific Data Extraction
## Applied to AAFC-SRDC Herbarium Digitization

**Document Type**: Policy and Operational Framework
**Date**: 2025-10-01
**Context**: AAFC-SRDC Herbarium Darwin Core Extraction Project
**Jurisdiction**: Saskatchewan, Canada (SRDC operations)
**Purpose**: Define equitable collaboration between curator expertise and AI processing

---

## Executive Summary

This framework documents the collaboration model developed during the AAFC-SRDC herbarium digitization project, where human curator expertise works alongside AI processing capabilities to extract structured Darwin Core data from 2,800+ herbarium specimens.

**Key Principles:**
- Curator scientific authority remains paramount
- AI provides processing scale and consistency
- Clear attribution of human vs. AI contributions
- Protection of curator expertise value
- Transparent documentation of decision-making

---

## Section 1: Project Context

### 1.1 The Digitization Challenge

**Problem:** 2,800 herbarium specimens at AAFC-SRDC need conversion from physical labels to digital Darwin Core records.

**Traditional Approach:**
- Manual transcription by curators: ~10-15 specimens/hour
- Total time: 186-280 hours of curator labor
- Cost: High; uses curator expertise for repetitive data entry

**AI-Augmented Approach:**
- Apple Vision OCR extraction: 95% accuracy
- Processing time: 4 hours for full collection
- Curator validation: Focus on scientific judgment, not data entry

**Value Proposition:** AI handles mechanical extraction; curator focuses on botanical expertise.

### 1.2 Collaboration Model

```
┌─────────────────────────────────────────┐
│      Human Domain (Curator/Devin)       │
│  • Taxonomic authority                  │
│  • Specimen quality assessment          │
│  • Scientific validation                │
│  • Publication decisions                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Collaborative Zone              │
│  • Data quality review                  │
│  • Error pattern identification         │
│  • Workflow optimization                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        AI Domain (OCR/Processing)       │
│  • Text extraction from images          │
│  • Field parsing and standardization    │
│  • Batch processing                     │
│  • Consistency checking                 │
└─────────────────────────────────────────┘
```

---

## Section 2: Authority Domains

### 2.1 Curator Exclusive Authority

**Scientific Decisions (Always Human):**
- Taxonomic identification and nomenclature
- Specimen quality and preservation assessment
- Geographic locality interpretation
- Collector identification and verification
- Date format disambiguation (e.g., 6/8/1942 → month/day or day/month)
- Habitat and ecology descriptions
- Conservation status determinations

**Rationale:** These require botanical expertise, local knowledge, and scientific training that AI cannot replicate.

### 2.2 AI Processing Authority

**Mechanical Extraction (AI Primary, Human Validation):**
- OCR text extraction from specimen labels
- Field identification and parsing
- Darwin Core field mapping
- Standardization to controlled vocabularies
- Batch consistency checking
- Format conversion and export

**Rationale:** These are pattern-matching tasks where AI provides speed and consistency.

### 2.3 Collaborative Validation

**Joint Review (Both Parties):**
- OCR quality assessment
- Error pattern identification
- Workflow efficiency improvements
- Quality control threshold setting
- Edge case resolution strategies

---

## Section 3: Attribution Framework

### 3.1 What Gets Attributed to Whom

**Human Contribution:**
```yaml
Curator (Devin):
  - Scientific expertise applied to validation
  - Taxonomic authority decisions
  - Quality control oversight
  - Geographic knowledge application
  - Dataset integrity assurance

Documentation:
  "Data extracted using AI-assisted OCR; scientific validation
   and taxonomic authority by [Curator Name], AAFC-SRDC"
```

**AI Contribution:**
```yaml
AI Processing:
  - Apple Vision OCR (95% accuracy)
  - Automated Darwin Core field mapping
  - Batch processing and standardization
  - Consistency checking across records

Documentation:
  "Automated extraction via Apple Vision OCR; processed using
   custom Darwin Core pipeline (Murphy, 2025)"
```

**Collaborative Contribution:**
```yaml
Human-AI Collaboration:
  - Iterative quality improvement
  - Error pattern identification and correction
  - Workflow optimization
  - Dataset completeness validation

Documentation:
  "Dataset created through human-AI collaborative digitization;
   curator validation ensures scientific accuracy while AI
   processing enables scale. See collaboration framework."
```

### 3.2 Publication Attribution

**For Data Publications (GBIF, etc.):**
```
Creator: [Curator Name] (Scientific authority)
Contributor: Devvyn Murphy (Technical implementation)
Rights Holder: Agriculture and Agri-Food Canada
Processing Method: AI-assisted OCR with curator validation
Quality Control: Curator review of 100% scientific determinations
```

**For Methods Publications:**
```
Author: Murphy, D. & [Curator Name if applicable]
Title: "Human-AI Collaborative Approach to Herbarium Digitization:
        Preserving Curator Expertise While Enabling Scale"
Affiliation: AAFC-SRDC, Saskatchewan
```

---

## Section 4: Value Exchange and Labor Considerations

### 4.1 Quantifying Contributions

**Time Investment:**

| Task | Manual (Curator Only) | AI-Assisted | Time Saved |
|------|----------------------|-------------|------------|
| Text extraction | 186-280 hours | 4 hours | 98% reduction |
| Field parsing | 40-60 hours | Automated | 100% reduction |
| Format standardization | 20-30 hours | Automated | 100% reduction |
| **Curator validation** | N/A | **40-60 hours** | **New capability** |
| **Total curator time** | **246-370 hours** | **40-60 hours** | **84% reduction** |

**Key Insight:** Curator time shifts from data entry to scientific validation—higher-value work.

**Value Analysis:**
- **AI provides:** Speed, consistency, mechanical accuracy
- **Human provides:** Scientific judgment, domain expertise, quality assurance
- **Combined value:** Dataset that is both complete AND scientifically accurate

### 4.2 Labor Impact Considerations

**Positive Impacts:**
- Curator focuses on scientific work, not data entry
- Enables processing of backlog collections
- Increases data accessibility for research
- Demonstrates value of curator expertise

**Concerns to Address:**
- Does productivity gain lead to workforce reduction?
- How is curator expertise valued in AI-augmented workflow?
- What happens if AI accuracy improves to 99%?
- How to prevent deskilling or expertise erosion?

**Saskatchewan Labor Context:**
- SRDC operates under Saskatchewan labor standards
- Federal AAFC employment also applies
- Collective bargaining considerations if applicable
- Need for policy protecting curator expertise value

---

## Section 5: Quality Control and Validation

### 5.1 Validation Protocol

**Two-Stage Quality Control:**

**Stage 1: AI Self-Check**
- Consistency across records
- Controlled vocabulary compliance
- Required field completeness
- Format standardization

**Stage 2: Curator Validation** (Authority Level: Human Exclusive)
- Scientific name accuracy
- Geographic locality verification
- Date disambiguation
- Collector identification
- Specimen quality notes

**Final Authority:** Curator approval required before publication.

### 5.2 Error Attribution

**When Errors Occur:**

| Error Type | Primary Responsibility | Resolution Authority |
|------------|----------------------|---------------------|
| OCR misread | AI limitation | Curator correction |
| Wrong field mapping | AI logic | Developer fix + curator review |
| Scientific misidentification | Human error | Curator correction |
| Format inconsistency | AI processing | Automated fix |
| Missing data | Source limitation | Curator judgment |

**Documentation:** All corrections tracked with attribution to prevent blame shifting.

---

## Section 6: Epistemic Justice Protections

### 6.1 Preventing Testimonial Injustice

**Risk:** AI system privileges automated extraction over curator knowledge.

**Protection:**
- Curator can override ANY AI decision
- Scientific determinations require curator approval
- Local knowledge explicitly valued in documentation
- Curator expertise cited in methodology

### 6.2 Preventing Hermeneutical Injustice

**Risk:** Lack of language to describe curator's unique contribution.

**Solution:** This framework provides vocabulary:
- "Curator validation" (not just "human review")
- "Scientific authority" (not just "quality check")
- "Botanical expertise" (not just "domain knowledge")
- "Human-AI collaboration" (not "automated with oversight")

### 6.3 Preventing Contributory Injustice

**Risk:** Curator contribution undervalued or unrecognized.

**Protection:**
- Clear attribution in all outputs
- Documentation of decision authority
- Preservation of expertise value in metrics
- Recognition of higher-value scientific work

---

## Section 7: Sustainability and Future Considerations

### 7.1 As AI Capabilities Improve

**Scenario:** OCR accuracy reaches 99%, requiring less curator validation.

**Framework Response:**
- Curator role shifts to strategic quality sampling
- More time for research applications of digitized data
- Expertise applied to harder specimens (degraded labels, etc.)
- New role: Training AI on edge cases

**Principle:** Technology augments expertise; doesn't replace it.

### 7.2 Workflow Evolution

**Current State:** Human-AI collaboration on equal footing.

**Future Scenarios:**

**Scenario A: AI Does More**
- Even higher OCR accuracy
- Automated taxonomic validation against databases
- Predictive text completion for damaged labels
→ Curator becomes scientific auditor and edge case specialist

**Scenario B: Human Does More**
- Complex specimens require more interpretation
- Research questions drive data extraction priorities
- Integration with molecular data requires expertise
→ Curator becomes research lead using AI tools

**Scenario C: New Hybrid Roles**
- "Digital Curator" role emerges
- Combines traditional expertise with AI tool proficiency
- Focuses on dataset-level quality and research applications

---

## Section 8: Implementation Checklist

### 8.1 For Institutional Adoption

**Before Starting:**
- [ ] Define curator authority domains
- [ ] Establish attribution protocols
- [ ] Set quality control thresholds
- [ ] Document validation workflow
- [ ] Clarify labor impact concerns

**During Processing:**
- [ ] Track time on curator validation
- [ ] Document AI vs. human corrections
- [ ] Record collaboration insights
- [ ] Monitor workload distribution
- [ ] Gather curator feedback

**After Completion:**
- [ ] Publish dataset with proper attribution
- [ ] Document lessons learned
- [ ] Assess impact on curator role
- [ ] Share methodology openly
- [ ] Contribute to policy discourse

### 8.2 For Policy Development

**What This Project Demonstrates:**
- [ ] AI can augment (not replace) scientific expertise
- [ ] Clear attribution protects both parties
- [ ] Curator authority must be preserved
- [ ] Value exchange can be equitable
- [ ] Documentation prevents exploitation

---

## Section 9: Recommendations for AAFC-SRDC

### 9.1 Immediate Actions

1. **Adopt This Framework**: Use as template for human-AI collaboration projects
2. **Document Attribution**: Apply attribution model to GBIF publication
3. **Track Metrics**: Monitor curator time allocation before/after
4. **Gather Feedback**: Debrief with curator on collaboration experience
5. **Share Learnings**: Contribute to herbarium digitization community

### 9.2 Policy Considerations

**For AAFC:**
- Develop guidelines for AI-assisted scientific work
- Ensure curator expertise value is preserved in metrics
- Consider new role definitions for AI-augmented workflows
- Protect against deskilling through continued training

**For Saskatchewan Context:**
- Position SRDC as leader in equitable AI integration
- Contribute to provincial AI governance discussions
- Model how to preserve scientific expertise while enabling automation
- Document for potential collective bargaining considerations

---

## Section 10: Conclusion

### 10.1 What We Learned

**This project demonstrates:**
1. AI and human expertise are complementary, not competitive
2. Clear authority domains enable productive collaboration
3. Attribution matters for both recognition and accountability
4. Curator expertise increases in value when focused on scientific judgment
5. Transparent documentation builds trust and prevents exploitation

### 10.2 Contribution to Broader Discourse

**This framework offers:**
- First documented model for herbarium human-AI collaboration
- Attribution template for scientific data extraction
- Labor impact analysis for AI-augmented workflows
- Saskatchewan-specific policy considerations
- Reusable patterns for other institutions

### 10.3 Final Statement

The AAFC-SRDC herbarium digitization project successfully demonstrates that **AI can dramatically increase processing efficiency while preserving and even enhancing the value of curator scientific expertise**.

The key is clear authority domains, transparent attribution, and commitment to epistemic justice. This framework ensures both human and AI contributions are recognized, expertise is protected, and the resulting dataset is both complete and scientifically sound.

---

## Appendices

### Appendix A: Technical Implementation
- OCR Pipeline Architecture
- Darwin Core Mapping Logic
- Quality Control Interfaces
- Export Format Specifications

### Appendix B: Attribution Templates
- GBIF Metadata Template
- Publication Citation Format
- Dataset Documentation Standards
- Methods Description Template

### Appendix C: Metrics and Analysis
- Time Savings Calculations
- Error Rate Analysis
- Contribution Attribution Data
- Curator Feedback Summary

### Appendix D: Related Frameworks
- Epistemic Boundaries Documentation
- Collaborative Equity Framework
- Adversarial Collaboration Protocols
- Knowledge Commons Structure

---

**Framework Status**: Operational and Applied to AAFC-SRDC Project
**Contact**: Devvyn Murphy
**Date**: October 1, 2025
**Location**: Saskatchewan, Canada

**Citation**: Murphy, D. (2025). *Human-AI Collaboration Framework for Scientific Data Extraction: Applied to AAFC-SRDC Herbarium Digitization*. Technical documentation, AAFC-SRDC Herbarium Project.

---

*This framework represents a practical implementation of equitable human-AI collaboration in scientific data work, designed to protect curator expertise while enabling the scale benefits of AI processing.*