# Double-anonymized repository plan for *Measurement*

Policy check date: 2026-08-16

## Official basis

Elsevier's double-anonymized review guidance states that authors must prevent
direct or indirect identification in reviewer-visible files. It also states that
the title page and cover letter remain separate from reviewer materials, while
other uploaded files are typically shared with reviewers.

- Elsevier, “Double anonymized peer review guidelines”:
  <https://www.elsevier.com/reviewer/what-is-peer-review/guidelines>
- Elsevier Support, “What are the requirements for double-anonymized peer
  review?” (updated 3 December 2025):
  <https://service.elsevier.com/app/answers/detail/a_id/28162/supporthub/publishing>

## Project decision

The Zenodo analysis record will list Siyu Cai as creator and therefore cannot be
linked directly from the reviewer-visible manuscript without weakening
anonymity. The submission will use the following separation:

1. Supply the complete code and derived outputs to reviewers as an anonymized
   supplementary archive with neutral filenames and no author metadata.
2. Create and publish the DOI-bearing Zenodo record immediately before
   submission (completed as published record `21973117`).
3. Report the Zenodo DOI to the editor in the title page, cover letter, and
   submission-system metadata only.
4. State transparently in the blind manuscript that a persistent identifier is
   withheld during double-anonymized review because its creator metadata is
   identifying.
5. Insert the DOI into the article after the double-anonymized review stage.

This approach preserves reviewer access to the reproducibility materials while
meeting the data-deposit requirement and avoiding an indirect author-identity
leak.
