# School Data Format

The repository stores school information in `data/schools.csv`. The dashboard keeps a local cached runtime workbook named `schools.xlsx`; `python -m app.sample_excel` can generate a local ignored `data/schools.xlsx` when a workbook is needed for a build or manual validation.

## Source CSV

Edit school-data updates in `data/schools.csv`, then bump `data/version.json` with a new `data_version` so GitHub sync can detect the change. Do not commit generated `.xlsx` files.

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
- Do not leave header cells blank.
- Keep `school_id` and `school_name` populated for every row.
- Blank optional cells are allowed; the app displays them as `Not provided`.
- Dates can be plain text for v1.
- Save source-controlled updates as `data/schools.csv`.
- If publishing updates through GitHub, update `data/version.json` with a new `data_version` so the app can detect the change.
- Do not commit generated `.xlsx` files to the normal repository history; they are local runtime/build artifacts only.

## Data Safety Warning

Do **not** store confidential, safeguarding, pupil-sensitive, staff-sensitive, medical, behavioural, or access-control information in GitHub-hosted CSV data. The GitHub sync design is intended only for public or approved operational information that is safe to distribute to all app users.
