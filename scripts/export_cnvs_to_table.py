import yaml
import pandas as pd
from pathlib import Path

def get_list(value):
    return value if isinstance(value, list) else []

def safe_get(d, key, default=""):
    return d.get(key, default) if isinstance(d, dict) else default

def build_row(base, gene, orpha, phenotype=None):
    return {
        **base,
        "genes_symbol": safe_get(gene, "symbol"),
        "genes_name": safe_get(gene, "name"),
        "hgnc_id": safe_get(gene, "hgnc_id"),
        "genes_entrez_id": safe_get(gene, "entrez_id"),
        "genes_ensembl_id": safe_get(gene, "ensembl_id"),
        "genes_uniprot_id": safe_get(gene, "uniprot_id"),
        "orphadata_orphacode": safe_get(orpha, "orphacode"),
        "orphadata_cause": safe_get(orpha, "cause"),
        "orphadata_definition": safe_get(orpha, "definition"),
        "orphadata_prevalence": safe_get(orpha, "prevalence"),
        "orphadata_phenotypes": safe_get(phenotype, "name") if phenotype else "",
        "orphadata_hpo_id": safe_get(phenotype, "hpo_id") if phenotype else "",
        "orphadata_omim": ";".join(get_list(orpha.get("omim"))),
        "orphadata_pubmed_ids": ";".join(get_list(orpha.get("pubmed_ids"))),
    }

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
            "pubmed_ids": ";".join(get_list(data.get("pubmed_ids"))),
            "wikipathways_id": data.get("wikipathways_id", ""),
        }

        genes = get_list(data.get("genes", [{}]))
        orphadata = get_list(data.get("orphadata", [{}]))

        for gene in genes:
            for orpha in orphadata:
                phenotypes = get_list(orpha.get("phenotypes"))
                if not phenotypes:
                    rows.append(build_row(base, gene, orpha))
                else:
                    for phenotype in phenotypes:
                        rows.append(build_row(base, gene, orpha, phenotype))

    return rows

def main():
    input_dir = Path("_cnvs")
    output_dir = Path("assets/data") # For public access
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
        "cnv", "locus", "chromosome", "start", "end", "description", "pubmed_ids",
        "genes_symbol", "genes_name", "hgnc_id", "genes_entrez_id", "genes_ensembl_id", "genes_uniprot_id",
        "wikipathways_id", "orphadata_orphacode", "orphadata_cause", "orphadata_definition",
        "orphadata_prevalence", "orphadata_phenotypes", "orphadata_hpo_id",
        "orphadata_omim", "orphadata_pubmed_ids"
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