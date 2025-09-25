import yaml
import pandas as pd
from pathlib import Path

def get_list(value):
    return value if isinstance(value, list) else []

def safe_get(d, key, default=""):
    return d.get(key, default) if isinstance(d, dict) else default

ORPHADATA_DEFAULT = {
    "orphacode": "NA",
    "cause": "NA",
    "definition": "NA",
    "prevalence": "NA",
    "phenotypes_obligate": [],
    "phenotypes_very_frequent": [],
    "phenotypes_frequent": [],
    "phenotypes_occasional": [],
    "omim": [],
    "pubmed_ids": []
}

def build_row(base, gene, orpha, phenotype=None, freq_category=None):
    freq_map = {
        "obligate": "orphadata_phenotypes_obligate",
        "very_frequent": "orphadata_phenotypes_very_frequent",
        "frequent": "orphadata_phenotypes_frequent",
        "occasional": "orphadata_phenotypes_occasional"
    }

    row = {
        **base,
        "genes_hgnc_symbol": safe_get(gene, "symbol"),
        "genes_hgnc_name": safe_get(gene, "name"),
        "genes_hgnc_id": safe_get(gene, "hgnc_id"),
        "genes_entrez_id": safe_get(gene, "entrez_id"),
        "genes_ensembl_id": safe_get(gene, "ensembl_id"),
        "genes_uniprot_id": safe_get(gene, "uniprot_id"),
        "orphadata_orphacode": safe_get(orpha, "orphacode"),
        "orphadata_cause": safe_get(orpha, "cause"),
        "orphadata_definition": safe_get(orpha, "definition"),
        "orphadata_prevalence": safe_get(orpha, "prevalence"),
        "orphadata_phenotypes_obligate": "",
        "orphadata_phenotypes_very_frequent": "",
        "orphadata_phenotypes_frequent": "",
        "orphadata_phenotypes_occasional": "",
        "orphadata_hpo_id": "",
        "orphadata_omim_id": ";".join(get_list(orpha.get("omim"))),
        "orphadata_pubmed_id": ";".join(get_list(orpha.get("pubmed_ids"))),
    }

    if phenotype and freq_category in freq_map:
        col_name = freq_map[freq_category]
        row[col_name] = safe_get(phenotype, "name")
        row["orphadata_hpo_id"] = safe_get(phenotype, "hpo_id")

    return row

def flatten_yaml_to_rows(yaml_path):
    rows = []
    with open(yaml_path, "r", encoding="utf-8") as f:
        documents = list(yaml.safe_load_all(f))

    for data in documents:
        if not data:
            continue

        base = {
            "cnv": data.get("cnv", ""),
            "locus": data.get("locus", ""),
            "chromosome": data.get("chromosome", ""),
            "start": data.get("start", ""),
            "end": data.get("end", ""),
            "description": data.get("description", ""),
            "pubmed_id": ";".join(get_list(data.get("pubmed_id"))),
            "wikipathways_id": data.get("wikipathways_id", ""),
        }

        genes = get_list(data.get("genes", [{}]))
        orphadata_list = get_list(data.get("orphadata"))
        if not orphadata_list:
            orphadata_list = [ORPHADATA_DEFAULT.copy()]

        for gene in genes:
            for orpha in orphadata_list:
                for freq_key, freq_cat in [
                    ("phenotypes_obligate", "obligate"),
                    ("phenotypes_very_frequent", "very_frequent"),
                    ("phenotypes_frequent", "frequent"),
                    ("phenotypes_occasional", "occasional"),
                ]:
                    phenotypes = get_list(orpha.get(freq_key))
                    if not phenotypes:
                        continue
                    for pheno in phenotypes:
                        row = build_row(base, gene, orpha, pheno, freq_cat)
                        rows.append(row)

    return rows

def main():
    input_dir = Path("_cnvs")
    output_dir = Path("assets/data")  # For public access
    output_dir.mkdir(exist_ok=True)

    yaml_files = list(input_dir.glob("*.yml")) + list(input_dir.glob("*.md"))
    all_rows = []

    for yml in yaml_files:
        try:
            all_rows.extend(flatten_yaml_to_rows(yml))
        except Exception as e:
            print(f"[ERROR] {yml.name}: {e}")

    df = pd.DataFrame(all_rows)

    column_order = [
        "cnv", "locus", "chromosome", "start", "end", "description", "pubmed_id",
        "genes_hgnc_symbol", "genes_hgnc_name", "genes_hgnc_id", "genes_entrez_id",
        "genes_ensembl_id", "genes_uniprot_id", "wikipathways_id",
        "orphadata_orphacode", "orphadata_cause", "orphadata_definition",
        "orphadata_prevalence",
        "orphadata_phenotypes_obligate",
        "orphadata_phenotypes_very_frequent",
        "orphadata_phenotypes_frequent",
        "orphadata_phenotypes_occasional",
        "orphadata_hpo_id",
        "orphadata_omim_id", "orphadata_pubmed_id"
    ]

    # Make sure all expected columns exist
    for col in column_order:
        if col not in df.columns:
            df[col] = ""

    df = df[column_order]

    df.to_csv(output_dir / "all_cnvs_table.csv", sep="\t", index=False)
    df.to_excel(output_dir / "all_cnvs_table.xlsx", index=False)
    print("Exported: all_cnvs_table.csv and all_cnvs_table.xlsx")

if __name__ == "__main__":
    main()
