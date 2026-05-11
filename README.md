# UAP Disclosure 2026 — A Forensic Anatomy

A reader's anatomy of the U.S. Department of War's **May 8, 2026** UAP/UFO disclosure. All findings derived from PDF metadata and OCR'd content of the 41 mission-report PDFs in the public release — no insider access, no leaks.

**Live site**: this repo is served via GitHub Pages.

## What's in this repo

- **`index.html`** — interactive forensic anatomy (single self-contained file, ~104 KB)
- **`forensic-report.md`** — long-form technical report, same findings in markdown
- **`README.md`** — this file

## What the analysis found

1. **Two of the largest documents aren't UFO reports.** D48 (181 pages, 1996 RTI booster-failure study) and D49 (113 pages, 1958–2000 Vandenberg launch summary) carry zero UAP content. Neither is publicly findable elsewhere (DTIC, RTI, NASA NTRS, archive.org all checked).
2. **D20's title metadata is wrong** on both location and year — labelled "Southern US 2020" but contains an F-16CM Eastern Syria mission from March 2023. The crew explicitly compared the targeting-pod signature against a known star ("RESULTS WERE DIFFERENT") — actively ruling out the most common prosaic explanation.
3. **At least four separate declassification cycles** were bundled into one release: USCENTCOM MDR 26-0038→26-0046, USCENTCOM MDR 26-0028 (with hidden renumbering), USCENTCOM MDR 25-0104 (D23 only), and Joint Staff JS-250710-TM8S / MDR 25-0094→25-0099 (D20 only). Two of the four were completed months before the May 2026 publication date.
4. **Eight numbered slots (D66–D73) reserved-but-empty** in the released sequence.
5. **JBIG2 numeric integrity verified**: every suspect value cross-checked three independent ways (Adobe OCR layer via pdftotext, tesseract on existing renders, fresh tesseract on 300-DPI re-renders). All agree. No detected substitutions.

## Methods

Standard open-source PDF forensics: `pdfinfo`, `exiftool`, `qpdf`, `pdftotext` (poppler), `pdfimages`, `tesseract`. All raw source files are public at https://www.war.gov/UFO/ — the analysis is fully reproducible.

## Source

- Department of War UAP release portal: https://www.war.gov/UFO/
- AARO: https://www.aaro.mil/
- AARO Historical Record Report Vol. 1 (March 2024): [PDF](https://media.defense.gov/2024/Mar/08/2003409233/-1/-1/0/DOPSR-CLEARED-508-COMPLIANT-HRRV1-08-MAR-2024-FINAL.PDF)

## Attribution

By **duckjustice**, with **Claude (Anthropic)** as research assistant. Synthesis and prose drafted with Claude; all findings independently verified against the source files.

## License

Free to share, cite, mirror, or critique. Adversarial review welcomed. If you find an error, open an issue or PR.
