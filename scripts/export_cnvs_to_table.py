"""Export the CNV pages (_cnvs/*.md) to the download files in assets/data.

Writes:
- CNVPathwayAtlas-data.xlsx: one row per CNV, gene, disorder and phenotype
- CNVPathwayAtlas-data.json: one record per CNV
- tsv/*.tsv: one table per entity (CNVs, genes, disorders, phenotypes, pathway genes)

Usage: python scripts/export_cnvs_to_table.py [path to cnv-data]   (default: ./cnv-data)
"""
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

SITE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "cnv-data").resolve()
CNVS_DIR = SITE_DIR / "_cnvs"
OUTPUT_DIR = SITE_DIR / "assets" / "data"

FREQUENCIES = ["obligate(100%)", "very_frequent(99-80%)", "frequent(79-30%)",
               "occasional(29-5%)", "very_rare(<4-1%)", "excluded(0%)"]

XLSX_COLUMNS = [
    "cnv", "locus", "chromosome", "start", "end", "region_GRCh37", "region_GRCh38",
    "description", "pubmed_ids",
    "genes_hgnc_symbol", "genes_hgnc_name", "genes_hgnc_id", "genes_entrez_id",
    "genes_ensembl_id", "genes_uniprot_id", "wikipathways_id", "pathway_genes",
    "orphadata_orphacode", "orphadata_cause", "orphadata_definition", "orphadata_prevalence",
    *[f"orphadata_phenotypes_{f}" for f in FREQUENCIES],
    "orphadata_hpo_id", "orphadata_omim_id",
]


def load_pages():
    pages = []
    for path in sorted(CNVS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        pages.append(yaml.safe_load(text.split("---\n")[1]))
    return pages


def load_pathway_genes():
    """Return the pathway gene table and {wikipathways_id: sorted protein-coding symbols}."""
    path = sorted((DATA_DIR / "data" / "latest").glob("pathway_genes_*.tsv"))[-1]
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    coding = df[(df["locus_group"] == "protein-coding gene") & (df["symbol"] != "")]
    return df, coding.groupby("wikipathways_id")["symbol"].apply(lambda s: sorted(set(s))).to_dict()


def entity_tables(pages):
    cnvs, genes, disorders, phenotypes = [], [], [], []
    for page in pages:
        cnvs.append({
            "cnv": page["cnv"], "locus": page["locus"],
            "region_GRCh37": page["region_hg19"], "region_GRCh38": page["region_hg38"],
            "chromosome": page["chromosome"], "start_GRCh37": page["start"],
            "end_GRCh37": page["end"], "size_GRCh37": page["size"],
            "start_GRCh38": page["start_hg38"], "end_GRCh38": page["end_hg38"], "size_GRCh38": page["size_hg38"],
            "cnv_types": ";".join(sorted({o["cnv_type"] for o in page["orphadata"] if o["cnv_type"]})),
            "orphacodes": ";".join(o["orphacode"] for o in page["orphadata"]),
            "wikipathways_id": page["wikipathways_id"], "pathway_name": page["pathway_name"],
            "gene_count": page["gene_count"], "protein_coding_count": page["protein_coding_count"],
            "pubmed_ids": ";".join(page["pubmed_ids"]), "description": page["description"],
        })
        for gene in page["genes"]:
            genes.append({"cnv": page["cnv"], **gene})
        for orpha in page["orphadata"]:
            disorders.append({
                "cnv": page["cnv"], "orphacode": orpha["orphacode"], "name": orpha["name"],
                "cause": orpha["cause"], "cnv_type": orpha["cnv_type"], "prevalence": orpha["prevalence"],
                "omim_ids": ";".join(orpha["omim"]), "definition": orpha["definition"],
            })
            for frequency in FREQUENCIES:
                for phenotype in orpha[f"phenotypes_{frequency}"]:
                    phenotypes.append({"orphacode": orpha["orphacode"], "hpo_id": phenotype["hpo_id"],
                                       "hpo_label": phenotype["name"], "frequency": frequency})
    return {
        "cnvs": pd.DataFrame(cnvs),
        "cnv_genes": pd.DataFrame(genes),
        "cnv_disorders": pd.DataFrame(disorders),
        "disorder_phenotypes": pd.DataFrame(phenotypes).drop_duplicates(),
    }


def xlsx_rows(page, pathway_symbols):
    base = {
        "cnv": page["cnv"], "locus": page["locus"], "chromosome": page["chromosome"],
        "start": page["start"], "end": page["end"],
        "region_GRCh37": page["region_hg19"], "region_GRCh38": page["region_hg38"],
        "description": page["description"], "pubmed_ids": ";".join(page["pubmed_ids"]),
        "wikipathways_id": page["wikipathways_id"],
        "pathway_genes": ";".join(pathway_symbols.get(page["wikipathways_id"], [])),
    }
    orphas = page["orphadata"] or [{"orphacode": "NA", "cause": "NA", "definition": "NA", "prevalence": "NA",
                                    "omim": [], **{f"phenotypes_{f}": [] for f in FREQUENCIES}}]
    for gene in page["genes"] or [{}]:
        gene_part = {
            "genes_hgnc_symbol": gene.get("symbol"), "genes_hgnc_name": gene.get("name"),
            "genes_hgnc_id": gene.get("hgnc_id"), "genes_entrez_id": gene.get("entrez_id"),
            "genes_ensembl_id": gene.get("ensembl_id"), "genes_uniprot_id": gene.get("uniprot_id"),
        }
        for orpha in orphas:
            orpha_part = {
                "orphadata_orphacode": orpha["orphacode"], "orphadata_cause": orpha["cause"],
                "orphadata_definition": orpha["definition"], "orphadata_prevalence": orpha["prevalence"],
                "orphadata_omim_id": ";".join(orpha["omim"]),
            }
            phenotype_rows = [(f, p) for f in FREQUENCIES for p in orpha[f"phenotypes_{f}"]]
            for frequency, phenotype in phenotype_rows or [(None, None)]:
                row = {**base, **gene_part, **orpha_part}
                if phenotype:
                    row[f"orphadata_phenotypes_{frequency}"] = phenotype["name"]
                    row["orphadata_hpo_id"] = phenotype["hpo_id"]
                yield row


def json_record(page, pathway_symbols):
    return {
        "cnv": page["cnv"], "locus": page["locus"], "chromosome": page["chromosome"],
        "start": page["start"], "end": page["end"],
        "region_GRCh37": page["region_hg19"], "region_GRCh38": page["region_hg38"],
        "description": page["description"], "pubmed_ids": page["pubmed_ids"],
        "wikipathways_id": page["wikipathways_id"],
        "pathway_genes": pathway_symbols.get(page["wikipathways_id"], []),
        "region_genes": [{k: g[k] for k in ("symbol", "name", "hgnc_id", "entrez_id", "ensembl_id", "uniprot_id")}
                         for g in page["genes"]],
        "orphadata": [{
            "orphacode": o["orphacode"], "name": o["name"], "cause": o["cause"],
            "definition": o["definition"], "prevalence": o["prevalence"], "omim_ids": o["omim"],
            "phenotypes": {f: o[f"phenotypes_{f}"] for f in FREQUENCIES},
        } for o in page["orphadata"]],
    }


def main():
    pages = load_pages()
    pathway_genes, pathway_symbols = load_pathway_genes()

    rows = [row for page in pages for row in xlsx_rows(page, pathway_symbols)]
    pd.DataFrame(rows).reindex(columns=XLSX_COLUMNS).to_excel(OUTPUT_DIR / "CNVPathwayAtlas-data.xlsx", index=False)

    records = [json_record(page, pathway_symbols) for page in pages]
    (OUTPUT_DIR / "CNVPathwayAtlas-data.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")

    tsv_dir = OUTPUT_DIR / "tsv"
    tsv_dir.mkdir(exist_ok=True)
    tables = entity_tables(pages)
    tables["pathway_genes"] = pathway_genes
    for name, df in tables.items():
        df.to_csv(tsv_dir / f"{name}.tsv", sep="\t", index=False, lineterminator="\n")

    print(f"Exported {len(pages)} CNVs: {len(rows)} XLSX rows, JSON, and {len(tables)} TSV tables")


if __name__ == "__main__":
    main()
