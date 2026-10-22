"""Build the CNV pages (_cnvs/*.md) and the data version file from the cnv-data repository.

Usage: python scripts/build_yaml_files.py [path to cnv-data]   (default: ./cnv-data)
"""
import json
import re
import shutil
import sys
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd
import yaml

SITE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "cnv-data").resolve()
sys.path.insert(0, str(DATA_DIR / "scripts"))

from cnv_input import cnv_key, load_input, parse_orphacodes, parse_region, split_list  # noqa: E402

LATEST_DIR = DATA_DIR / "data" / "latest"
CNVS_DIR = SITE_DIR / "_cnvs"
PATHWAYS_OUT = SITE_DIR / "assets" / "pathways"
VERSION_OUT = SITE_DIR / "_data" / "data_version.yml"

FREQUENCIES = {
    "phenotypes_obligate(100%)": "Phenotypes_Obligate(100%)",
    "phenotypes_very_frequent(99-80%)": "Phenotypes_Very_frequent(99-80%)",
    "phenotypes_frequent(79-30%)": "Phenotypes_Frequent(79-30%)",
    "phenotypes_occasional(29-5%)": "Phenotypes_Occasional(29-5%)",
    "phenotypes_very_rare(<4-1%)": "Phenotypes_Very_rare(<4-1%)",
    "phenotypes_excluded(0%)": "Phenotypes_Excluded(0%)",
}


def latest(pattern):
    files = sorted(LATEST_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No file matches {pattern} in {LATEST_DIR}")
    return files[-1]


def read_table(pattern, sep="\t"):
    return pd.read_csv(latest(pattern), sep=sep, dtype=str, keep_default_na=False)


def parse_phenotypes(value):
    """Return [{name, hpo_id}] from 'term (HP:0000001); term (HP:0000002)'."""
    result = []
    for part in filter(None, (p.strip() for p in value.split(";"))):
        match = re.match(r"(.+?)\s*\(?(HP:\d{7})\)?$", part)
        result.append({"name": match.group(1), "hpo_id": match.group(2)} if match else {"name": part, "hpo_id": None})
    return result


def cnv_type(cause):
    """Return the CNV type word found in the cause label, e.g. 'distal microdeletion' -> 'deletion'."""
    for word in ("deletion", "duplication", "triplication"):
        if word in (cause or ""):
            return word
    return None


def build_orphadata(value, orpha):
    entries = []
    for code, cause in parse_orphacodes(value):
        info = orpha.get(code)
        entry = {"orphacode": code, "cause": cause, "cnv_type": cnv_type(cause),
                 "in_orphadata": info is not None,
                 "name": info["Name"] if info else None,
                 "definition": (info["Definition"] or None) if info else None,
                 "prevalence": info["Prevalence"] if info else None}
        for key, column in FREQUENCIES.items():
            entry[key] = parse_phenotypes(info[column]) if info else []
        entry["omim"] = split_list(info["OMIM"]) if info else []
        entries.append(entry)
    return entries


def build_genes(key, mapping, hgnc, pathway_hgnc_ids):
    genes = []
    for _, row in mapping[mapping["cnv"] == key].iterrows():
        info = hgnc.get(row["hgnc_id"], {})
        genes.append({
            "symbol": row["symbol"] or row["input_symbol"],
            "input_symbol": row["input_symbol"] if row["input_symbol"] != row["symbol"] else None,
            "name": info.get("name") or None,
            "hgnc_id": info.get("hgnc_id") or None,
            "entrez_id": info.get("entrez_id") or None,
            "ensembl_id": info.get("ensembl_gene_id") or None,
            "uniprot_id": info.get("uniprot_ids", "").split("|")[0] or None,
            "omim_id": info.get("omim_id", "").split("|")[0] or None,
            "locus_group": info.get("locus_group") or None,
            "in_pathway": row["hgnc_id"] in pathway_hgnc_ids if row["hgnc_id"] else False,
        })
    return genes


def write_page(path, front_matter):
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, sort_keys=False, allow_unicode=True)
        f.write("---\n")


def copy_pathways(wp_ids):
    shutil.rmtree(PATHWAYS_OUT, ignore_errors=True)
    PATHWAYS_OUT.mkdir(parents=True)
    for wp in wp_ids:
        for ext in ("svg", "gpml"):
            source = DATA_DIR / "data" / "pathways" / f"{wp}.{ext}"
            if source.exists():
                shutil.copy(source, PATHWAYS_OUT / source.name)
            else:
                print(f"[WARN] No {ext.upper()} file for {wp}")


def write_data_version(sources):
    version = (DATA_DIR / "version.txt").read_text().strip()
    data = {
        "version": version,
        "retrieved": sources.get("retrieved", "")[:10],
        "orphadata_release": sources.get("orphadata", {}).get("definitions", {}).get("release_date", "")[:10],
        "hgnc_release": parsedate_to_datetime(sources["hgnc"]["last_modified"]).date().isoformat(),
    }
    VERSION_OUT.parent.mkdir(exist_ok=True)
    VERSION_OUT.write_text(yaml.dump(data, sort_keys=False))
    return version


def main():
    df_input = load_input()
    orpha = read_table("orphadata_filtered_*.csv", sep=",").set_index("OrphaCode").to_dict("index")
    for code, info in orpha.items():
        info["OrphaCode"] = code
    hgnc = read_table("hgnc_filtered_*.tsv").set_index("hgnc_id", drop=False).to_dict("index")
    mapping = read_table("gene_mapping_*.tsv")
    pathway_genes = read_table("pathway_genes_*.tsv")
    pathway_ids = pathway_genes[pathway_genes["hgnc_id"] != ""].groupby("wikipathways_id")["hgnc_id"].apply(set).to_dict()
    sources = json.loads((LATEST_DIR / "sources.json").read_text())

    version = write_data_version(sources)
    copy_pathways(sorted({wp for wp in df_input["wikipathways_id"] if wp}))

    CNVS_DIR.mkdir(exist_ok=True)
    written = set()
    for _, row in df_input.iterrows():
        key = cnv_key(row)
        chrom19, start19, end19 = parse_region(row["region_hg19"])
        chrom38, start38, end38 = parse_region(row["region_hg38"])
        genes = build_genes(key, mapping, hgnc, pathway_ids.get(row["wikipathways_id"], set()))

        front_matter = {
            "layout": "cnv-page",
            "title": f"{key} Copy Number Variation",
            "cnv": key,
            "locus": row["locus"],
            "region_hg19": row["region_hg19"],
            "chromosome": chrom19,
            "start": start19,
            "end": end19,
            "size": end19 - start19 if start19 is not None else None,
            "region_hg38": row["region_hg38"],
            "chromosome_hg38": chrom38,
            "start_hg38": start38,
            "end_hg38": end38,
            "size_hg38": end38 - start38 if start38 is not None else None,
            "description": row["description"] or None,
            "pubmed_ids": split_list(row["pubmed_id"]),
            "gene_count": len(genes),
            "protein_coding_count": sum(g["locus_group"] == "protein-coding gene" for g in genes),
            "genes": genes,
            "wikipathways_id": row["wikipathways_id"] or None,
            "pathway_name": row["pathway_name"] or None,
            "orphadata": build_orphadata(row["orphacodes"], orpha),
            "data_version": version,
        }
        filename = re.sub(r"[:\s]", "", key) + ".md"
        write_page(CNVS_DIR / filename, front_matter)
        written.add(filename)

    for stale in CNVS_DIR.glob("*.md"):
        if stale.name not in written:
            print(f"Removing {stale.name}: CNV is not in the input")
            stale.unlink()

    print(f"{len(written)} CNV pages written to {CNVS_DIR} (data {version})")


if __name__ == "__main__":
    main()
