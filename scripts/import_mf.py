import re
from datetime import datetime
from sqlmodel import Session, select, create_engine, SQLModel
from app.models import Transaction

DATA_FILE = "data/mf_raw.txt"
DB_URL = "sqlite:///data/finance_v2.db"

def parse_amount(s):
    # Remove commas and currency symbols
    s = s.replace(",", "").replace("円", "").strip()
    return float(s)

def main():
    engine = create_engine(DB_URL)
    # Ensure DB exists
    SQLModel.metadata.create_all(engine)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f]
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found.")
        return

    transactions = []
    current_year = 2025 # Default
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for Year Range header
        m_range = re.match(r"(\d{4})/\d{1,2}/\d{1,2}\s*-\s*(\d{4})/\d{1,2}/\d{1,2}", line)
        if m_range:
            current_year = int(m_range.group(1))
            i += 1
            continue
            
        m_date = re.match(r"(\d{1,2})/(\d{1,2})\(.\)", line)
        if m_date:
            month = int(m_date.group(1))
            day = int(m_date.group(2))
            
            date_obj = datetime(current_year, month, day)
            
            if i + 2 >= len(lines):
                break
                
            description = lines[i+1] # Content
            amount_str = lines[i+2] # Amount
            
            if not re.match(r"^-?[\d,]+$", amount_str.replace("円", "")):
                 i += 1
                 continue

            try:
                amount = parse_amount(amount_str)
            except ValueError:
                i += 1
                continue
                
            j = i + 3
            details = []
            while j < len(lines):
                next_line = lines[j]
                if re.match(r"\d{1,2}/\d{1,2}\(.\)", next_line) or \
                   re.match(r"\d{4}/\d{1,2}/\d{1,2}", next_line):
                    break
                details.append(next_line)
                j += 1
            
            source = "Unknown"
            category = "Uncategorized"
            
            is_transfer = False
            for d in details:
                if "(振替)" in d:
                    is_transfer = True
                
                parts = d.split("\t")
                if len(parts) >= 2:
                    source = parts[0].strip()
                    category = parts[1].strip()
                    if len(parts) > 2 and parts[2].strip():
                        category += f" / {parts[2].strip()}"
            
            if is_transfer and category == "Uncategorized":
                category = "振替"
                non_transfer_lines = [d for d in details if "(振替)" not in d and d != "未設定"]
                if non_transfer_lines:
                    source = non_transfer_lines[0]
            
            tx = Transaction(
                date=date_obj,
                description=description,
                amount=amount,
                source=source,
                category=category
            )
            transactions.append(tx)
            
            i = j
        else:
            i += 1

    print(f"Parsed {len(transactions)} transactions.")
    
    with Session(engine) as session:
        count = 0
        for tx in transactions:
            existing = session.exec(
                select(Transaction).where(
                    Transaction.date == tx.date,
                    Transaction.description == tx.description,
                    Transaction.amount == tx.amount,
                    Transaction.source == tx.source
                )
            ).first()
            
            if not existing:
                session.add(tx)
                count += 1
        
        session.commit()
        print(f"Imported {count} new transactions.")

if __name__ == "__main__":
    main()
