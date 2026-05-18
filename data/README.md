# School Data

Binary Excel files are intentionally **not committed** to this repository.

The source-controlled school data is:

```text
data/schools.csv
```

The app keeps runtime data as a local cached Excel workbook named `schools.xlsx`. For development and builds, scripts can generate a local ignored workbook at:

```text
data/schools.xlsx
```

Production data workflow:

1. Edit approved non-confidential school data in `data/schools.csv` using the format in `docs/EXCEL_FORMAT.md`.
2. Bump `data/version.json` with a new `data_version` so installed apps detect the update.
3. Let the app sync download `schools.csv`, validate it, and generate cached `schools.xlsx` at runtime.
4. Do **not** commit `schools.xlsx` to the repo.
5. Upload built `.exe`, `.dmg`, and installer artifacts to GitHub Releases rather than committing them.

Never store confidential, safeguarding, pupil-sensitive, staff-sensitive, medical, behavioural, or access-control information in GitHub-hosted files.
