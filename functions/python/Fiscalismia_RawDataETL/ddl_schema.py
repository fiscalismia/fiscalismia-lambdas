# ddl_schema.py
#
# Defines the structural mapping of each table in the Finance Google Sheet to
# pandas iloc indices (0-based).
#
# Excel column → 0-based index reference:
#   A=0  B=1  C=2  D=3  E=4  F=5  G=6  H=7  I=8  J=9  K=10 L=11 M=12 N=13 O=14
#   P=15 Q=16 R=17 S=18 T=19 U=20 V=21 W=22 X=23 Y=24 Z=25 AA=26 AB=27
#   AJ=35 AK=36 AL=37 AM=38 AN=39 AO=40
#   AP=41 AQ=42 AR=43 AS=44 AT=45 AU=46 AV=47 AW=48
#
# Sheet layout (0-based row index):
#   Row 0: empty filler row
#   Row 1: table name annotations
#   Row 2: date range annotations
#   Row 3: column headers  ← HEADER_ROW
#   Row 4+: data rows      ← DATA_START_ROW

HEADER_ROW = 3
DATA_START_ROW = 4

# ── TABLE_VAR_EXPENSES ────────────────────────────────────────────────────────
# Source: columns B:I  (iloc 1–8, slice end is exclusive → slice(1, 9))
# Single contiguous block; no sub-sections.
TABLE_VAR_EXPENSES = {
    "col_slice": slice(1, 9),
    "col_names": [
        "description",
        "category",
        "store",
        "cost",
        "purchasing_date",
        "is_planned",
        "contains_indulgence",
        "sensitivities",
    ],
    # Values in col 0 (relative) that mark non-data rows to skip
    "skip_markers": {"description", "border"},
}

# ── TABLE_FIXED_COSTS ─────────────────────────────────────────────────────────
# Source: columns K:O  (iloc 10–14, slice(10, 15))
# Multi-section: multiple "Date: X - Y" group headers are embedded in the data
# area. The date range for each group becomes effective_date / expiration_date.
#
# Row types (identified by col 0 relative = K):
#   "Date:"    → date-range header; col 1 relative (L) holds "DD.MM.YYYY - DD.MM.YYYY"
#   "category" → sub-header row  → skip
#   "SUM"      → totals row      → skip
#   other      → actual data row
TABLE_FIXED_COSTS = {
    "col_slice": slice(10, 15),
    "col_names": [
        "category",
        "description",
        "monthly_interval",
        "billed_cost",
        "monthly_cost",
    ],
    # effective_date and expiration_date are derived from the embedded "Date:" rows
    "derived_col_names": ["effective_date", "expiration_date"],
    "skip_markers": {"category", "SUM", "border"},
    "date_marker": "Date:",
    # Offset (relative to col_slice start) where the date string lives on a date row
    "date_value_col_offset": 1,
}

# ── TABLE_INVESTMENTS ─────────────────────────────────────────────────────────
# Source: columns Q:AB  (iloc 16–27, slice(16, 28))
TABLE_INVESTMENTS = {
    "col_slice": slice(16, 28),
    "col_names": [
        "execution_type",
        "description",
        "isin",
        "investment_type",
        "marketplace",
        "units",
        "price_per_unit",
        "total_price",
        "fees",
        "execution_date",
        "pct_of_profit_taxed",
        "profit_amt",
    ],
    "skip_markers": {"execution_type", "Investment", "border"},
}

# ── TABLE_INCOME ──────────────────────────────────────────────────────────────
# Source: columns AJ:AM  (iloc 35–38, slice(35, 39))
# Multi-section: embedded "Date: X - Y" rows separate income periods.
TABLE_INCOME = {
    "col_slice": slice(35, 39),
    "col_names": [
        "description",
        "type",
        "monthly_interval",
        "value",
    ],
    "derived_col_names": ["effective_date", "expiration_date"],
    "skip_markers": {"monthly revenue", "description", "SUM", "border"},
    "date_marker": "Date:",
    "date_value_col_offset": 1,
}

# ── TABLE_NEW_FOOD_ITEMS ──────────────────────────────────────────────────────
# Source: columns AP:AW  (iloc 41–48, slice(41, 49))
TABLE_NEW_FOOD_ITEMS = {
    "col_slice": slice(41, 49),
    "col_names": [
        "food_item",
        "brand",
        "store",
        "main_macro",
        "kcal_amount",
        "weight",
        "price",
        "last_update",
    ],
    "skip_markers": {"food_item", "[100 grams]", "border"},
}
