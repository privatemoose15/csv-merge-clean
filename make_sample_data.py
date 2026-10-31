#!/usr/bin/env python3
"""Write deliberately messy sample files to samples/before/ for demoing merge_clean.py.

Three exports of the same customer list, each broken in the ways real exports are:
different header spellings, mixed date formats, stray spaces, blank rows, a BOM,
an old Windows (cp1252) encoding, and the same people appearing in more than one file.
"""
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

OUT = Path(__file__).parent / "samples" / "before"


def write_csv(path: Path, rows: list, encoding: str):
    path.write_text("\n".join(",".join(r) for r in rows) + "\n", encoding=encoding)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Website sign-ups: "CSV UTF-8" from Excel (has a BOM), UK dates, padded values
    write_csv(OUT / "signups_website.csv", [
        ["First Name", "Last Name", "Email", "Phone", "Signup Date", "Plan"],
        ["Sarah", "Jones", "sarah.jones@example.com", "07700 900123", "05/03/2024", "Pro"],
        ["  Tom ", "Baker", "tom.baker@example.com ", "07700 900456", "12/03/2024", "Basic"],
        ["Priya", "Shah", "priya.shah@example.com", "07700 900789", "2024-03-14", "Pro"],
        ["", "", "", "", "", ""],
        ["Liam", "O'Neill", "liam.oneill@example.com", "07700 900321", "TBC", "Basic"],
        ["Grace", "Kim", "grace.kim@example.com", "07700 900654", "18/03/2024", "Team"],
    ], encoding="utf-8-sig")

    # 2. Old CRM: cp1252 encoding (accents break UTF-8 readers), SHOUTY headers,
    #    written-out dates, upper-case emails, an exact duplicate row
    write_csv(OUT / "crm_export_old.csv", [
        ["FIRST NAME", "LAST NAME", "EMAIL ", "PHONE", "SIGNUP DATE", "PLAN"],
        ["Sarah", "Jones", "Sarah.Jones@Example.com", "07700 900123", "5 March 2024", "Pro"],
        ["José", "García", "jose.garcia@example.com", "07700 900987", "07-03-2024", "Basic"],
        ["Tom", "Baker", "TOM.BAKER@EXAMPLE.COM", "07700 900456", "12 Mar 2024", "Basic"],
        ["Zoë", "Adams", "zoe.adams@example.com", "07700 900111", "20/03/2024", "Team"],
        ["Zoë", "Adams", "zoe.adams@example.com", "07700 900111", "20/03/2024", "Team"],
    ], encoding="cp1252")

    # 3. Shop export: real Excel date cells mixed with text dates, a blank row, phone kept as text
    wb = Workbook()
    ws = wb.active
    ws.title = "Customers"
    ws.append(["first_name", "last_name", "e-mail", "phone", "signup_date", "plan"])
    ws.append(["Priya", "Shah", "priya.shah@example.com", "07700 900789", datetime(2024, 3, 14), "Pro"])
    ws.append(["Grace", "Kim", " grace.kim@example.com", "07700 900654", "18/03/2024", "Team"])
    ws.append([None] * 6)
    ws.append(["Ahmed", "Hassan", "ahmed.hassan@example.com", "07700 900222", datetime(2024, 3, 22), "Pro"])
    ws.append(["Chloe", "Evans", "chloe.evans@example.com", "07700 900333", "2024/03/25", "Basic"])
    wb.save(OUT / "shop_customers.xlsx")

    print(f"Wrote 3 messy files to {OUT}")


if __name__ == "__main__":
    main()
