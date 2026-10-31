# csv-merge-clean

Merge several messy CSV/Excel exports into one clean, de-duplicated file — in one command.

Built for the common job: *"I've got three exports from different systems, the headers don't
match, the dates are all over the place and half the customers are in there twice."*

## What it fixes

| Problem in the input | What happens |
|---|---|
| Headers spelt differently (`First Name`, `FIRST NAME`, `first_name`, `FirstName`) | Matched and merged into one `first_name` column |
| Dates in mixed formats (`05/03/2024`, `5 March 2024`, `2024/03/25`, real Excel date cells) | All converted to `2024-03-05` (ISO). UK day-first by default, `--us-dates` for US files |
| Values that aren't dates (`TBC`) | Left untouched and listed in a warning, never silently blanked |
| Stray spaces, double spaces, Excel's non-breaking spaces | Trimmed |
| `Sarah.Jones@Example.com` vs `sarah.jones@example.com` | Emails lower-cased so duplicates actually match |
| Same person in more than one file | Duplicate rows removed (after cleaning, so near-duplicates are caught) |
| Blank rows | Dropped |
| Old Windows exports (`José` turning into `Jos�`) | Encoding detected (UTF-8, UTF-8 with BOM, Windows-1252) |
| Phone numbers / IDs losing leading zeros | Everything is read as text, so `07700…` stays `07700…` |

Every output row keeps a `source_file` column, so you can trace where it came from.

## Before → after

Three input files in [`samples/before/`](samples/before/) — 16 rows between them:

```text
signups_website.csv (UTF-8 with BOM)
  First Name,Last Name,Email,Phone,Signup Date,Plan
  Sarah,Jones,sarah.jones@example.com,07700 900123,05/03/2024,Pro
    Tom ,Baker,tom.baker@example.com ,07700 900456,12/03/2024,Basic
  ,,,,,
  Liam,O'Neill,liam.oneill@example.com,07700 900321,TBC,Basic

crm_export_old.csv (Windows-1252)
  FIRST NAME,LAST NAME,EMAIL ,PHONE,SIGNUP DATE,PLAN
  Sarah,Jones,Sarah.Jones@Example.com,07700 900123,5 March 2024,Pro
  José,García,jose.garcia@example.com,07700 900987,07-03-2024,Basic
  Tom,Baker,TOM.BAKER@EXAMPLE.COM,07700 900456,12 Mar 2024,Basic

shop_customers.xlsx
  first_name | last_name | e-mail                 | phone        | signup_date          | plan
  Priya      | Shah      | priya.shah@example.com | 07700 900789 | (Excel date cell)    | Pro
  Grace      | Kim       |  grace.kim@example.com | 07700 900654 | 18/03/2024           | Team
```

```console
$ python merge_clean.py samples/before/* -o samples/after/cleaned.csv
Warning: 1 unparseable value(s) in 'signup_date' left as-is: TBC
Files: 3 | Rows in: 16 | Blank rows dropped: 2 | Duplicates removed: 5 | Rows out: 9
Saved: samples/after/cleaned.csv
```

Result in [`samples/after/cleaned.csv`](samples/after/cleaned.csv) (also as [`.xlsx`](samples/after/cleaned.xlsx)):

| first_name | last_name | email | phone | signup_date | plan | source_file |
|---|---|---|---|---|---|---|
| Sarah | Jones | sarah.jones@example.com | 07700 900123 | 2024-03-05 | Pro | crm_export_old.csv |
| José | García | jose.garcia@example.com | 07700 900987 | 2024-03-07 | Basic | crm_export_old.csv |
| Tom | Baker | tom.baker@example.com | 07700 900456 | 2024-03-12 | Basic | crm_export_old.csv |
| Zoë | Adams | zoe.adams@example.com | 07700 900111 | 2024-03-20 | Team | crm_export_old.csv |
| Priya | Shah | priya.shah@example.com | 07700 900789 | 2024-03-14 | Pro | shop_customers.xlsx |
| Grace | Kim | grace.kim@example.com | 07700 900654 | 2024-03-18 | Team | shop_customers.xlsx |
| Ahmed | Hassan | ahmed.hassan@example.com | 07700 900222 | 2024-03-22 | Pro | shop_customers.xlsx |
| Chloe | Evans | chloe.evans@example.com | 07700 900333 | 2024-03-25 | Basic | shop_customers.xlsx |
| Liam | O'Neill | liam.oneill@example.com | 07700 900321 | TBC | Basic | signups_website.csv |

## Install

Python 3.9+.

```bash
pip install -r requirements.txt
```

## Usage

```bash
python merge_clean.py file1.csv file2.xlsx file3.csv -o cleaned.xlsx
```

| Option | What it does |
|---|---|
| `-o, --output` | Output file. `.xlsx` writes Excel, anything else writes CSV. Default `cleaned.csv` |
| `--date-cols COL ...` | Which columns hold dates. Default: any column named like `*_date`, `date_*` or `dob` |
| `--us-dates` | Read `03/04/2024` as 4 March (US). Default is UK: 3 April |
| `--rename OLD=NEW ...` | Map header variants onto one name, e.g. `--rename "Email Address=email"` |
| `--dedupe-on COL ...` | Count rows as duplicates when only these columns match, e.g. `--dedupe-on email`. The first one found is kept. Default: every column must match |

## Limitations

- Reads the first sheet of each Excel file only.
- A date like `03/04/2024` is genuinely ambiguous: the tool follows the `--us-dates` setting for the
  whole run. If one file is UK and another is US, clean them in separate runs.
- In a day-first run, a value like `12/31/2024` is still read as 31 December (there is no 31st month).
  It is not flagged, so check files that might mix UK and US dates.
- Phone numbers, names and currency values are trimmed, not reformatted.

## Run the demo yourself

```bash
python make_sample_data.py          # rebuilds samples/before/
python merge_clean.py samples/before/* -o samples/after/cleaned.csv
pip install -r requirements-dev.txt && pytest
```
