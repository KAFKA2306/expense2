"""Parse MoneyForward raw data and export to CSV."""
import csv
import re
from pathlib import Path
from datetime import datetime


def parse_mf_raw(raw_file: Path) -> list[dict]:
    """Parse mf_raw.txt into transaction records."""
    transactions = []
    current_year = None
    
    with open(raw_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for date range header (e.g., "2025/12/1 - 2025/12/31")
        if re.match(r"\d{4}/\d{1,2}/\d{1,2}\s*-", line):
            match = re.match(r"(\d{4})", line)
            if match:
                current_year = match.group(1)
            i += 1
            continue
        
        # Check for transaction date (e.g., "12/26(金)")
        date_match = re.match(r"(\d{1,2})/(\d{1,2})\([月火水木金土日]\)", line)
        if date_match and current_year:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            date = f"{current_year}-{month:02d}-{day:02d}"
            
            # Next line is description
            i += 1
            if i >= len(lines):
                break
            description = lines[i]
            
            # Next line is amount
            i += 1
            if i >= len(lines):
                break
            amount_str = lines[i].replace(",", "")
            try:
                amount = float(amount_str)
            except ValueError:
                i += 1
                continue
            
            # Parse remaining lines for category and source
            i += 1
            category = "未分類"
            subcategory = "未分類"
            source = "未設定"
            
            # Check for (振替) indicator
            if i < len(lines) and lines[i] == "(振替)":
                category = "振替"
                i += 1
            
            # Check for source/category line (tab-separated)
            if i < len(lines):
                parts = lines[i].split("\t")
                if len(parts) >= 3:
                    source = parts[0]
                    category = parts[1]
                    subcategory = parts[2]
                    i += 1
                elif len(parts) == 1 and not re.match(r"\d{1,2}/\d{1,2}\([月火水木金土日]\)", lines[i]) and not re.match(r"\d{4}/\d{1,2}/\d{1,2}\s*-", lines[i]):
                    # Single source without category
                    source = parts[0]
                    i += 1
                    # Check next line for more source info
                    if i < len(lines) and not re.match(r"\d{1,2}/\d{1,2}\([月火水木金土日]\)", lines[i]) and not re.match(r"\d{4}/\d{1,2}/\d{1,2}\s*-", lines[i]):
                        potential_source = lines[i]
                        if not potential_source.startswith("-") and not potential_source.replace(",", "").replace("-", "").isdigit():
                            source = potential_source
                            i += 1
            
            transactions.append({
                "date": date,
                "description": description,
                "amount": amount,
                "category": f"{category} / {subcategory}" if subcategory != "未分類" else category,
                "source": source,
                "currency": "JPY"
            })
        else:
            i += 1
    
    return transactions


def main():
    data_dir = Path(__file__).parent.parent / "data"
    raw_file = data_dir / "mf_raw.txt"
    csv_file = data_dir / "transactions.csv"
    
    transactions = parse_mf_raw(raw_file)
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "description", "amount", "category", "source", "currency"])
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"Exported {len(transactions)} transactions to {csv_file}")


if __name__ == "__main__":
    main()
