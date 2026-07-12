# Data manifest

## Raw third-party archive

- Dataset: Survey of Working Arrangements and Attitudes (SWAA)
- Provider and access page: WFH Research, `https://wfhresearch.com/data/`
- Access condition: researchers create an account to access anonymized microdata, subject to the provider's data-use terms
- Release used: June 2026 earnings-restricted data package
- Main internal CSV: `WFHdata_May26.csv`
- Alternative no-earnings-requirement release: not used
- Example archive filename: `WFH_Code_and_Data_May2020_to_May2026.zip`
- Recorded archive size: 106,672,824 bytes
- Recorded SHA256: `AEB9F0CFBA280BD8595F1D93897851FADE9274FB5483E99FB8A4F92E5F72734E`
- Internal CSV size recorded in the archive: 439,262,815 bytes
- Variable dictionary: `Variable dictionary May 2020 to May 2026.pdf`
- License file: `LicenseMay2020toMay2026.txt`

## Provider-defined earnings eligibility

The earnings-restricted release applies the provider’s prior-year earnings criteria: at least USD 20,000 through March 2021, a transition toward USD 10,000 during April–December 2021, and at least USD 10,000 in the relevant prior year from 2022 onward. The manuscript and code identify this release explicitly.

## Analytic timing

Job dissatisfaction, desired WFH, and employer-planned WFH were observed for 37,434 records from July 2025 through February 2026. The fully adjusted complete-case association model retained 15,355 records from September–December 2025 because commute time was unavailable in July–August 2025 and January–February 2026. Ranking models use July–December 2025 for training and January–February 2026 for temporal-holdout evaluation.

## Reproduction

Any local archive filename may be supplied through `--data-zip`, but the pipeline stops when its SHA256 value differs from the value above unless the user deliberately passes `--no-hash-check`. The submission package does not redistribute raw SWAA records.
