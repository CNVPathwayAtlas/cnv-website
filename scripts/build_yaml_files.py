import re
import yaml
import pandas as pd
from pathlib import Path
import sys

def get_latest_csv(dir_path, pattern):
    files = sorted(dir_path.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(f"No files found matching: {pattern} in {dir_path}")
    return files[0]

def parse_gene_info(gene_symbol, hgnc_df):
    row = hgnc_df[hgnc_df["symbol"] == gene_symbol]
    if row.empty:
        return {"symbol": gene_symbol, "info": "Not found in HGNC"}
    else:
        return {
            "symbol": gene_symbol,
            "name": row.iloc[0]["name"],
            "ensembl": row.iloc[0]["ensembl_gene_id"],
            "entrez": row.iloc[0]["entrez_id"]
        }

def parse_disease_info(orpha_code, orpha_df):
    row = orpha_df[orpha_df["ORPHAcode"] == orpha_code]
    if row.empty:
        return {"ORPHAcode": orpha_code, "info": "Not found in Orphadata"}
    else:
        return {
            "ORPHAcode": orpha_code,
            "name": row.iloc[0]["preferred_name"],
            "phenotypes": row.iloc[0]["phenotypes"]
        }

def main():
     # Input file path
    input_dir = Path("cnv-data/data/input")
    excel_path = input_dir / "cnv_data.xlsx"

     # Filtered CSV data in data/latest
    latest_dir = Path("cnv-data/data/latest")
    print(f"Looking for latest HGNC CSV in: {latest_dir}")
    hgnc_csv = get_latest_csv(latest_dir, "hgnc_filtered_*.csv")
    print(f"Found HGNC CSV: {hgnc_csv}")

    print(f"Looking for latest Orphadata CSV in: {latest_dir}")
    orpha_csv = get_latest_csv(latest_dir, "orphadata_filtered_*.csv")
    print(f"Found Orphadata CSV: {orpha_csv}")

    if not excel_path.exists():
        raise FileNotFoundError(f"Input Excel file not found: {excel_path}")

    # Output path
    yaml_dir = Path("_cnvs")
    yaml_dir.mkdir(parents=True, exist_ok=True)

    # Load input files
    print(f"Loading Excel: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"Loading HGNC CSV: {hgnc_csv}")
    hgnc = pd.read_csv(hgnc_csv, sep="\t")
    print(f"Loading Orphadata CSV: {orpha_csv}")
    orpha = pd.read_csv(orpha_csv, sep="\t")

    for _, row in df.iterrows():
        locus = str(row["locus"]).replace(":", "-")
        genes = [g.strip() for g in str(row["genes"]).split(",") if g.strip()]
        orpha_codes = re.findall(r"\d+", str(row["Orphacodes"]))

        yaml_dict = {
            "wikipathway": row.get("WikiPathway ID", ""),
            "locus": row.get("locus", ""),
            "region": row.get("region", ""),
            "description": row.get("Description", ""),
            "genes": [parse_gene_info(g, hgnc) for g in genes],
            "diseases": [parse_disease_info(int(code), orpha) for code in orpha_codes],
        }

        output_file = yaml_dir / f"{locus}.yml"
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(yaml_dict, f, sort_keys=False, allow_unicode=True)

        print(f"Generated: {output_file.name}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)