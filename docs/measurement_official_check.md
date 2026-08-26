# Measurement official-policy check

## Verification status

**VERIFIED against the official Measurement Guide for Authors on 2026-08-16.**

- Journal: *Measurement*, ISSN 0263-2241.
- Official guide: <https://www.sciencedirect.com/journal/measurement/publish/guide-for-authors>
- Official scope page: <https://www.sciencedirect.com/journal/measurement/about/aims-and-scope>
- Evidence used: the official guide text supplied by the user and an independent retrieval of the same ScienceDirect guide through a web extraction service restricted to official Elsevier/ScienceDirect domains.
- Recheck requirement: the dynamic guide must be checked again immediately before submission because Elsevier may revise policies.

## Scope decision for this manuscript

The manuscript can fit *Measurement* only if it is presented as an advance in **evaluation procedures for performance analysis of measurement systems and algorithms**, not as an application of standard machine-learning models to a sensor dataset.

The paper must therefore make the following measurement-science contribution explicit:

1. a leakage-controlled temporal evaluation procedure for a measurement system;
2. a reference-budget decision curve for recalibration under deployment-period shift;
3. an explicit failure boundary showing when lightweight output updating is insufficient;
4. metrologically disciplined reporting of predictive error, calibration slope, reference support, denominator stability, and reproducibility;
5. a cover-letter explanation of how the work advances measurement-system performance evaluation.

The paper must not claim that PLS, Random Forest, XGBoost, or linear output calibration are new algorithms. It must not use “accuracy,” “uncertainty,” “precision,” or “drift” loosely. The available dataset supports predictive-error and temporal-shift evaluation; it does not provide a complete traceable measurement-uncertainty budget or a causal isolation of physical sensor drift.

## Binding submission requirements

| Item | Official requirement | Project decision |
|---|---|---|
| Article type | Original research papers accepted; original papers, reviews, and letters must not exceed 30 pages | Submit as an original research paper; target 24–27 pages including references to preserve margin |
| Review model | Double anonymized | Produce separate title page and anonymized manuscript; remove authors, affiliations, acknowledgments, funding identities, and other identifying residues from the blind file |
| Abstract | Concise, factual, stand-alone, no more than 250 words | Target 220–240 words; avoid citations and non-standard abbreviations |
| Keywords | 1–7 English keywords | Use 6 keywords |
| Highlights | Required; separate editable file; 3–5 bullets; each at most 85 characters including spaces | Prepare 5 independently character-counted bullets |
| Graphical abstract | Encouraged, separate file; at least 531 × 1328 px (h × w) or proportional; readable at 5 × 13 cm | Optional; defer until the main manuscript stabilizes |
| Editable source | `.doc/.docx` or `.tex`; PDF is not an acceptable source file | Use Elsevier LaTeX source plus PDF for checking |
| Sections | Clearly defined and numbered; abstract not numbered | Use numbered IMRaD sections and numbered subsections |
| References | Any consistent style accepted at submission; journal style is numbered square brackets in order of appearance | Draft directly in numbered Elsevier style; include DOI where available |
| Figures | Separate files; vector EPS/PDF preferred; raster rules vary by artwork type | Use vector PDFs for all four figures; retain 300-dpi PNG checks only as auxiliary files |
| Tables | Editable text; no vertical rules or cell shading | Use LaTeX `booktabs` tables |
| Research data | Option C: deposit and cite/link data, or explain why sharing is impossible | Cite the source Zenodo dataset; deposit analysis code and derived non-duplicative outputs in a persistent repository before submission |
| Data statement | Required at submission | Include a Data and code availability section |
| CRediT | Required | Add a CRediT contribution statement after author roles are known |
| Funding | Funding source and sponsor role must be declared; recommended no-funding sentence when applicable | Keep a verified placeholder until the author supplies the funding status |
| Competing interests | Declarations tool required; upload resulting `.doc/.docx` | Prepare a separate declaration file; do not infer the author’s answer |
| Generative AI | Use in manuscript preparation must be disclosed before references; authors retain full responsibility | Include an Elsevier-compatible disclosure naming Codex/OpenAI and its limited roles; disclose reproducible AI-assisted figure-code generation as appropriate |
| Acknowledgments | In title-page file only for double-anonymized review | Keep out of the anonymized manuscript |
| Supplementary material | Submit with the manuscript; files appear online as received | Provide audit details, complete result matrices, and run manifests as supplementary material |

## Measurement-facing editorial risks

1. **Desk-reject risk: ordinary ML application.** Mitigation: lead with the evaluation procedure and measurement decision, not model performance rankings.
2. **Desk-reject risk: insufficient metrological context.** Mitigation: define measurand, reference concentration, predictive error, calibration, reference panel, and the absence of a full uncertainty budget.
3. **Desk-reject risk: sensor-only scope redirected to Measurement: Sensors.** Mitigation: emphasize generalizable evaluation of a measurement system rather than sensor fabrication or sensor-material development.
4. **Desk-reject risk: weak novelty.** Mitigation: use search-bounded novelty language and demonstrate the combined contribution of time ordering, frozen holdouts, absolute budgets, failure cases, and ratio-denominator diagnostics.
5. **Desk-reject risk: incomplete reproducibility.** Mitigation: provide configurations, sampled row IDs, checksums, environment, code, and an exact rerun.

## Remaining author-owned information

The guide is now verified, but the following cannot be inferred and must remain placeholders until supplied: author names/order, affiliations, corresponding author, ORCIDs, funding/grant details, competing interests, acknowledgments, and final CRediT allocation.
