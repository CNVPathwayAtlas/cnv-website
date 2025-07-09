import pandas as pd
from pathlib import Path
import yaml
import re


def get_latest_csv(folder: Path, pattern: str) -> Path:
    """Find the latest CSV file matching the pattern (e.g. orphadata_filtered_*.csv)."""
    files = sorted(folder.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(f"No files found matching: {pattern}")
    return files[0]


def parse_gene_info(gene_symbol: str, hgnc_df: pd.DataFrame) -> dict:
    match = hgnc_df[hgnc_df["symbol"] == gene_symbol.strip()]
    if not match.empty:
        return match.iloc[0].dropna().to_dict()
    return {"symbol": gene_symbol.strip(), "note": "not found in HGNC"}


def parse_disease_info(code: int, orpha_df: pd.DataFrame) -> dict:
    match = orpha_df[orpha_df["ORPHAcode"] == code]
    if not match.empty:
        return match.iloc[0].dropna().to_dict()
    return {"ORPHAcode": code, "note": "not found in Orphadata"}


def main():
    # Input file path
    input_dir = Path("cnv-data/data/input")
    excel_path = input_dir / "cnv_data.xlsx"

    # Filtered CSV data in data/latest
    latest_dir = Path("cnv-data/data/latest")
    hgnc_csv = get_latest_csv(latest_dir, "hgnc_filtered_*.csv")
    orpha_csv = get_latest_csv(latest_dir, "orphadata_filtered_*.csv")

    # Output path
    yaml_dir = Path("_cnvs")
    yaml_dir.mkdir(parents=True, exist_ok=True)

    # Load input files
    df = pd.read_excel(excel_path)
    hgnc = pd.read_csv(hgnc_csv, sep="\t")
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

        print(f"✅ Generated: {output_file.name}")


if __name__ == "__main__":
    main()
