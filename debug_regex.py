import re

def extract_metadata_from_filename(filename):
    """Extract date and source from filename."""
    print(f"Testing filename: {filename}")
    
    # JPM: JPM_..._YYYY-MM-DD_...pdf
    jpm_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if "JPM" in filename and jpm_match:
        print("  Matched JPM")
        return {"date": jpm_match.group(1), "source": "JPM", "year": int(jpm_match.group(1)[:4])}
    
    # BIS: r_qtYYMM.pdf
    bis_match = re.search(r'r_qt(\d{2})(\d{2})', filename)
    if bis_match:
        print("  Matched BIS")
        yy = bis_match.group(1)
        mm = bis_match.group(2)
        year = 1900 + int(yy) if int(yy) >= 90 else 2000 + int(yy)
        return {"date": f"{year}-{mm}-01", "source": "BIS", "year": year}

    # FT: ..._YYYY-MM-DD.json
    ft_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if filename.endswith('.json') and ft_match:
        print("  Matched FT")
        return {"date": ft_match.group(1), "source": "FT", "year": int(ft_match.group(1)[:4])}

    # FCIC
    if "Financial Crisis Enquiry Report" in filename:
        print("  Matched FCIC")
        return {"date": "2011-01-01", "source": "FCIC", "year": 2011}

    print("  Matched NONE")
    return {"date": "1900-01-01", "source": "Unknown", "year": 1900}

# Test cases
filenames = [
    "JPM_U_S__Fixed_Income_Ma_2008-10-04_469066.pdf", # Worked
    "JPM_US_Fixed_Income_Mark_2008-07-12_454228.pdf", # Failed
    "JPM_U_S__Fixed_Income_Ma_2008-10-25_472987.pdf"  # Failed
]

for f in filenames:
    print(extract_metadata_from_filename(f))
