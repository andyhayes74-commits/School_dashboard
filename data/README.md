# School Data Placeholder

Binary Excel files are intentionally **not committed** to this repository.

For development, the source-controlled sample data is:

```text
data/schools.csv
```

The app and build scripts can generate a local ignored Excel workbook at:

```text
data/schools.xlsx
```

Production data workflow:

1. Edit or export approved non-confidential school data using the format in `docs/EXCEL_FORMAT.md`.
2. Generate or place `schools.xlsx` locally for builds or releases.
3. Do **not** commit `schools.xlsx` to the repo.
4. Upload built `.exe`, `.dmg`, and installer artifacts to GitHub Releases rather than committing them.

Never store confidential, safeguarding, pupil-sensitive, staff-sensitive, medical, behavioural, or access-control information in GitHub-hosted files.
