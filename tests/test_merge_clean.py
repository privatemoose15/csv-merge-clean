import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent


def run(tmp_path, *extra):
    subprocess.run([sys.executable, ROOT / "make_sample_data.py"], check=True)
    out = tmp_path / "cleaned.csv"
    inputs = sorted((ROOT / "samples" / "before").iterdir())
    result = subprocess.run([sys.executable, ROOT / "merge_clean.py", *inputs, "-o", out, *extra],
                            check=True, capture_output=True, text=True)
    return pd.read_csv(out, dtype=str), result.stdout


def test_merges_dedupes_and_drops_blanks(tmp_path):
    df, stdout = run(tmp_path)
    assert len(df) == 9
    assert "Blank rows dropped: 2" in stdout
    assert "Duplicates removed: 5" in stdout


def test_headers_aligned_across_files(tmp_path):
    df, _ = run(tmp_path)
    assert list(df.columns) == ["first_name", "last_name", "email", "phone",
                                "signup_date", "plan", "source_file"]


def test_dates_iso_and_bad_dates_kept(tmp_path):
    df, stdout = run(tmp_path)
    dates = df.set_index("email")["signup_date"]
    assert dates["sarah.jones@example.com"] == "2024-03-05"   # was 05/03/2024 and "5 March 2024"
    assert dates["priya.shah@example.com"] == "2024-03-14"    # was an Excel date cell
    assert dates["liam.oneill@example.com"] == "TBC"
    assert "TBC" in stdout


def test_cp1252_accents_survive(tmp_path):
    df, _ = run(tmp_path)
    assert {"José", "Zoë"} <= set(df["first_name"])


def test_phone_leading_zero_kept(tmp_path):
    df, _ = run(tmp_path)
    assert df["phone"].str.startswith("07").all()
