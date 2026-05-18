"""Application configuration and constants."""

from __future__ import annotations

APP_NAME = "School Information Dashboard"
COMPANY_NAME = "World of Swimming"
CACHE_APP_DIR_NAME = "SchoolInfoDashboard"
DATA_DIR_NAME = "data"
EXCEL_FILENAME = "schools.xlsx"
CSV_SAMPLE_FILENAME = "schools.csv"
VERSION_FILENAME = "version.json"
SCHOOLS_SHEET_NAME = "schools"
REQUIRED_COLUMNS = ("school_id", "school_name")
NOT_PROVIDED = "Not provided"

# Placeholder raw GitHub URLs for v1. Replace OWNER/REPOSITORY/BRANCH with the
# real repository path that will host public non-confidential school data.
REMOTE_VERSION_URL = (
    "https://raw.githubusercontent.com/OWNER/REPOSITORY/BRANCH/data/version.json"
)
REMOTE_EXCEL_URL = (
    "https://raw.githubusercontent.com/OWNER/REPOSITORY/BRANCH/data/schools.xlsx"
)

DEFAULT_THEME = {
    "company_name": COMPANY_NAME,
    "app_title": APP_NAME,
    "primary_colour": "#23408F",
    "secondary_colour": "#F5F7FA",
    "accent_colour": "#3B82F6",
    "text_colour": "#1F2937",
}
