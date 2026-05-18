# Excel Data Format

The dashboard reads school information from `schools.xlsx`. To avoid committing binary files, the repository stores sample data at `data/schools.csv`; `python -m app.sample_excel` can generate a local ignored `data/schools.xlsx` when a workbook is needed for a build or release.

## Required Sheet Name

The workbook must contain a sheet named exactly:

```text
schools
```

## Required Columns

| Column | Purpose |
|---|---|
| `school_id` | Unique internal school identifier. This is used by the app but hidden from the main display. |
| `school_name` | Display name shown in search results and the school dropdown. |

## Recommended Columns

| Column | Purpose |
|---|---|
| `address` | School address |
| `phone` | Main phone number |
| `email` | Main contact email address |
| `website` | Public website URL |
| `opening_times` | General opening hours |
| `term_dates` | Current term date information |
| `inset_days` | INSET / training days |
| `breakfast_club` | Breakfast club details |
| `after_school_club` | After-school club details |
| `notes` | Additional public notes |

Extra columns are allowed and will be displayed automatically. Do not change the required column names.

## Example Table

| school_id | school_name | address | phone | email | website | opening_times |
|---|---|---|---|---|---|---|
| SCH001 | Bluewater Primary School | 12 Harbour Road, Brighton | 01273 000 101 | office@bluewater.example | www.bluewater-primary.example | Mon-Fri 08:30-15:30 |
| SCH002 | Oak Lane Academy | Oak Lane, Manchester | 0161 000 202 | info@oaklane.example | https://oaklane-academy.example | Mon-Fri 08:45-15:15 |

## Editing Rules

- Keep one row per school.
- Do not use merged cells.
- Do not leave header cells blank.
- Keep `school_id` and `school_name` populated for every row.
- Blank optional cells are allowed; the app displays them as `Not provided`.
- Dates can be plain text for v1.
- Save the file as `.xlsx`, not `.csv` or `.xls`.
- If publishing updates through GitHub, update `data/version.json` with a new `data_version` so the app can detect the change.
- Do not commit generated `.xlsx` files to the normal repository history; upload release data/build artifacts through the approved release process.

## Data Safety Warning

Do **not** store confidential, safeguarding, pupil-sensitive, staff-sensitive, medical, behavioural, or access-control information in GitHub-hosted Excel data. The GitHub sync design is intended only for public or approved operational information that is safe to distribute to all app users.
