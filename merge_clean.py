#!/usr/bin/env python3
"""Merge, clean and de-duplicate CSV/Excel files."""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# Excel's "CSV UTF-8" adds a BOM; older Windows exports are cp1252 (where £ lives).
# latin-1 decodes any byte, so it is the last resort that never fails.
ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")


def tidy_name(col) -> str:
    """'  First Name ' -> 'first_name'"""
    return re.sub(r"[^0-9a-z]+", "_", str(col).strip().lower()).strip("_")


def match_key(col) -> str:
    """'First Name', 'first_name', 'FirstName', 'first-name' -> 'firstname'"""
    return re.sub(r"[^0-9a-z]", "", str(col).lower())


def unique_names(cols) -> list:
    """Suffix clashes ('Email', 'EMAIL ') so pandas doesn't choke on duplicate columns."""
    seen, out = {}, []
    for c in cols:
        seen[c] = seen.get(c, 0) + 1
        out.append(c if seen[c] == 1 else f"{c}_{seen[c]}")
    return out


def load(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path, dtype=str)
    else:
        for enc in ENCODINGS:
            try:
                df = pd.read_csv(path, dtype=str, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
    df.columns = [tidy_name(c) for c in df.columns]
    return df


def align_headers(frames, renames: dict):
    """Give the same header the same name in every file, named after the first spelling seen."""
    canonical = {}
    for df in frames:
        names = (renames.get(match_key(c), c) for c in df.columns)
        df.columns = unique_names(canonical.setdefault(match_key(n), n) for n in names)


def is_date_col(name: str) -> bool:
    # whole-word match, so 'candidate' and 'updated_by' are left alone
    return bool(re.search(r"(^|_)(date|dob)(_|$)", name))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inputs", nargs="+", type=Path, help="CSV/XLSX files")
    p.add_argument("-o", "--output", type=Path, default=Path("cleaned.csv"))
    p.add_argument("--date-cols", nargs="*", help="Default: any column named like *date* or dob")
    p.add_argument("--us-dates", action="store_true", help="Parse as MM/DD (default DD/MM)")
    p.add_argument("--rename", nargs="*", default=[], metavar="OLD=NEW",
                   help="Map header variants onto one name, e.g. 'Email Address=email'")
    p.add_argument("--dedupe-on", nargs="*", metavar="COL",
                   help="Treat rows as duplicates when these columns match (default: all columns)")
    args = p.parse_args()

    renames = {}
    for pair in args.rename:
        old, sep, new = pair.partition("=")
        if not sep:
            sys.exit(f"Error: --rename expects OLD=NEW, got '{pair}'")
        renames[match_key(old)] = tidy_name(new)

    frames = [load(f) for f in args.inputs]
    align_headers(frames, renames)
    df = pd.concat([f.assign(source_file=path.name) for f, path in zip(frames, args.inputs)],
                   ignore_index=True)
    rows_in = len(df)

    # Trim and collapse whitespace (incl. Excel's non-breaking spaces), treat blanks as missing
    df = df.apply(lambda s: s.str.replace(r"\s+", " ", regex=True).str.strip())
    df = df.mask(df == "")

    data_cols = [c for c in df.columns if c != "source_file"]
    df = df.dropna(how="all", subset=data_cols)

    # Emails are case-insensitive; lower-case them so duplicates actually match
    for col in (c for c in data_cols if "email" in c):
        df[col] = df[col].str.lower()

    # Standardise dates to ISO (YYYY-MM-DD)
    date_cols = [tidy_name(c) for c in args.date_cols] if args.date_cols else [
        c for c in data_cols if is_date_col(c)]
    dedupe_cols = [tidy_name(c) for c in args.dedupe_on] if args.dedupe_on else data_cols
    missing = [c for c in date_cols + dedupe_cols if c not in df.columns]
    if missing:
        sys.exit(f"Error: no such column(s): {', '.join(missing)}. Have: {', '.join(data_cols)}")
    for col in date_cols:
        # format="mixed" parses each value on its own; without it pandas guesses one
        # format from the first value and silently drops every row that differs
        parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=not args.us_dates, format="mixed")
        bad = parsed.isna() & df[col].notna()
        if bad.any():
            print(f"Warning: {bad.sum()} unparseable value(s) in '{col}' left as-is: "
                  f"{', '.join(df.loc[bad, col].unique()[:5])}")
        df[col] = parsed.dt.strftime("%Y-%m-%d").where(~bad, df[col])

    before = len(df)
    df = df.drop_duplicates(subset=dedupe_cols)

    if args.output.suffix.lower() == ".xlsx":
        df.to_excel(args.output, index=False)
    else:
        df.to_csv(args.output, index=False)

    print(f"Files: {len(args.inputs)} | Rows in: {rows_in} | Blank rows dropped: {rows_in - before} | "
          f"Duplicates removed: {before - len(df)} | Rows out: {len(df)}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
