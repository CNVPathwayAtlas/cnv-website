import yaml
import pandas as pd
import requests
from pathlib import Path
from glob import glob

from _site.scripts.build_yaml_files import parse_phenotypes

def get_latest_csv(directory: Path, pattern: str) -> Path:
    """Get the most recent CSV file matching pattern."""
    files = list(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern} in {directory}")
    return max(files, key=lambda f: f.stat().st_mtime)


def load_protein_coding_genes(latest_dir: Path) -> set:
    """Load protein-coding gene symbols from HGNC dataset."""
    print(f"Looking for latest HGNC CSV in: {latest_dir}")
    hgnc_csv = get_latest_csv(latest_dir, "hgnc_filtered_*.csv")
    print(f"Found HGNC CSV: {hgnc_csv}")
    
    df = pd.read_csv(hgnc_csv, sep="\t", usecols=["symbol", "locus_group"], low_memory=False)
    protein_coding = df[df["locus_group"] == "protein-coding gene"]["symbol"].tolist()
    print(f"  -> Found {len(protein_coding)} protein-coding genes")
    return set(protein_coding)


def fetch_wikipathways_json():
    """Fetch pathway info from WikiPathways."""
    url = "https://www.wikipathways.org/json/findPathwaysByXref.json"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json().get("pathwayInfo", [])


def map_ids_to_hgnc_bridgedb(ids: list, source_code: str) -> dict:
    """
    Use BridgeDb web service to map gene IDs to HGNC symbols.
    
    Args:
        ids: List of gene identifiers
        source_code: BridgeDb source code (L=NCBI/Entrez, En=Ensembl)
    
    Returns a dict: {id: hgnc_symbol}
    """
    if not ids:
        return {}
    
    mapping = {}
    # BridgeDb batch mapping endpoint for Human genes
    base_url = f"https://webservice.bridgedb.org/Human/xrefsBatch/{source_code}"
    
    # Process in batches of 100 to avoid URL length limits
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i + batch_size]
        try:
            response = requests.post(
                base_url,
                data="\n".join(batch),
                headers={"Content-Type": "text/plain"},
                timeout=30
            )
            if response.status_code == 200:
                # Parse response: each line is "query_id\tSource Name\ttarget1,target2,..."
                for line in response.text.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        query_id = parts[0]
                        # Find HGNC symbol in mappings (format: H:SYMBOL)
                        for target in parts[2].split(","):
                            target = target.strip()
                            if target.startswith("H:"):
                                hgnc_symbol = target[2:]  # Remove "H:" prefix
                                mapping[query_id] = hgnc_symbol
                                break
        except requests.RequestException as e:
            print(f"[WARN] BridgeDb batch request failed for {source_code}: {e}")
    
    return mapping


def get_pathway_genes_hgnc(pathways: list, protein_coding_genes: set) -> dict:
    """
    For each pathway, get protein-coding gene HGNC symbols.
    Maps NCBI/Ensembl IDs via BridgeDb, then filters to protein-coding only.
    Returns: {pathway_id: "GENE1;GENE2;..."}
    """
    pathway_ids = {}
    all_ncbi_ids = set()
    all_ensembl_ids = set()
    
    def split_ids(raw_str, prefix):
        """Split IDs that may be separated by comma or semicolon."""
        ids = []
        if not raw_str:
            return ids
        for part in raw_str.split(","):
            for subpart in part.split(";"):
                clean_id = subpart.replace(prefix, "").strip()
                if clean_id and not clean_id.startswith(("ensembl:", "ncbigene:")):
                    ids.append(clean_id)
        return ids
    
    for pw in pathways:
        if pw.get("species") != "Homo sapiens":
            continue
        
        pw_id = pw.get("id", "")
        ncbi_ids = split_ids(pw.get("ncbigene", ""), "ncbigene:")
        ensembl_ids = split_ids(pw.get("ensembl", ""), "ensembl:")
        
        all_ncbi_ids.update(ncbi_ids)
        all_ensembl_ids.update(ensembl_ids)
        pathway_ids[pw_id] = {"ncbi_ids": ncbi_ids, "ensembl_ids": ensembl_ids}
    
    # Batch map all IDs to HGNC symbols via BridgeDb
    print(f"Mapping {len(all_ncbi_ids)} NCBI Gene IDs via BridgeDb...")
    ncbi_to_hgnc = map_ids_to_hgnc_bridgedb(list(all_ncbi_ids), "L")
    print(f"  -> Mapped {len(ncbi_to_hgnc)} NCBI IDs")
    
    print(f"Mapping {len(all_ensembl_ids)} Ensembl IDs via BridgeDb...")
    ensembl_to_hgnc = map_ids_to_hgnc_bridgedb(list(all_ensembl_ids), "En")
    print(f"  -> Mapped {len(ensembl_to_hgnc)} Ensembl IDs")
    
    # Combine mapped genes for each pathway, filtering to protein-coding only
    result = {}
    for pw_id, data in pathway_ids.items():
        genes = set()
        for ncbi_id in data["ncbi_ids"]:
            if ncbi_id in ncbi_to_hgnc:
                symbol = ncbi_to_hgnc[ncbi_id]
                if symbol in protein_coding_genes:
                    genes.add(symbol)
        for ensembl_id in data["ensembl_ids"]:
            if ensembl_id in ensembl_to_hgnc:
                symbol = ensembl_to_hgnc[ensembl_id]
                if symbol in protein_coding_genes:
                    genes.add(symbol)
        result[pw_id] = ";".join(sorted(genes)) if genes else ""
    
    return result

def get_list(value):
    return value if isinstance(value, list) else []

def safe_get(d, key, default=""):
    return d.get(key, default) if isinstance(d, dict) else default

ORPHADATA_DEFAULT = {
    "orphacode": "NA",
    "cause": "NA",
    "definition": "NA",
    "prevalence": "NA",
    "phenotypes_obligate(100%)": [],
    "phenotypes_very_frequent(99-80%)": [],
    "phenotypes_frequent(79-30%)": [],
    "phenotypes_occasional(29-5%)": [],
    "phenotypes_very_rare(<4-1%)": [],
    "phenotypes_excluded(0%)": [],
    "omim": [],
}

def build_row(base, gene, orpha, phenotype=None, freq_category=None):
    freq_map = {
        "obligate(100%)": "orphadata_phenotypes_obligate(100%)",
        "very_frequent(99-80%)": "orphadata_phenotypes_very_frequent(99-80%)",
        "frequent(79-30%)": "orphadata_phenotypes_frequent(79-30%)",
        "occasional(29-5%)": "orphadata_phenotypes_occasional(29-5%)",
        "very_rare(<4-1%)": "orphadata_phenotypes_very_rare(<4-1%)",
        "excluded(0%)": "orphadata_phenotypes_excluded(0%)"
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
        "orphadata_phenotypes_obligate(100%)": "",
        "orphadata_phenotypes_very_frequent(99-80%)": "",
        "orphadata_phenotypes_frequent(79-30%)": "",
        "orphadata_phenotypes_occasional(29-5%)": "",
        "orphadata_phenotypes_very_rare(<4-1%)": "",
        "orphadata_phenotypes_excluded(0%)": "",
        "orphadata_hpo_id": "",
        "orphadata_omim_id": ";".join(get_list(orpha.get("omim"))),
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
            "region_GRCh37": data.get("region", ""),
            "region_GRCh38": data.get("region_hg38", ""),
            "description": data.get("description", ""),
            "pubmed_ids": ";".join(get_list(data.get("pubmed_ids"))),
            "wikipathways_id": data.get("wikipathways_id", ""),
        }

        genes = get_list(data.get("genes", [{}]))
        orphadata_list = get_list(data.get("orphadata"))
        if not orphadata_list:
            orphadata_list = [ORPHADATA_DEFAULT.copy()]

        for gene in genes:
            for orpha in orphadata_list:
                has_phenotypes = False
                for freq_key, freq_cat in [
                    ("phenotypes_obligate(100%)", "obligate(100%)"),
                    ("phenotypes_very_frequent(99-80%)", "very_frequent(99-80%)"),
                    ("phenotypes_frequent(79-30%)", "frequent(79-30%)"),
                    ("phenotypes_occasional(29-5%)", "occasional(29-5%)"),
                    ("phenotypes_very_rare(<4-1%)", "very_rare(<4-1%)"),
                    ("phenotypes_excluded(0%)", "excluded(0%)")
                ]:
                    phenotypes = get_list(orpha.get(freq_key))
                    if not phenotypes:
                        continue
                    has_phenotypes = True
                    for pheno in phenotypes:
                        row = build_row(base, gene, orpha, pheno, freq_cat)
                        rows.append(row)
                
                # If no phenotypes, still generate a row for this gene/orpha combo
                if not has_phenotypes:
                    row = build_row(base, gene, orpha)
                    rows.append(row)

    return rows


def main():
    cnvs_dir = Path("_cnvs")
    latest_dir = Path("cnv-data/data/latest")
    output_dir = Path("assets/data")
    output_dir.mkdir(exist_ok=True)

    # Load protein-coding genes from HGNC first
    protein_coding_genes = load_protein_coding_genes(latest_dir)

    # Fetch WikiPathways data and build pathway->genes mapping
    print("Fetching WikiPathways data...")
    all_pathways = fetch_wikipathways_json()
    pathway_to_genes = get_pathway_genes_hgnc(all_pathways, protein_coding_genes)
    print(f"Built pathway gene mapping for {len(pathway_to_genes)} pathways")

    # Process YAML files
    yaml_files = list(cnvs_dir.glob("*.yml")) + list(cnvs_dir.glob("*.md"))
    print(f"Found {len(yaml_files)} YAML files in {cnvs_dir}")
    all_rows = []

    for yml in yaml_files:
        try:
            all_rows.extend(flatten_yaml_to_rows(yml))
        except Exception as e:
            print(f"[ERROR] {yml.name}: {e}")

    df = pd.DataFrame(all_rows)
    print(f"Generated {len(df)} rows from YAML files")

    # Add pathway genes column
    if "wikipathways_id" in df.columns:
        df["pathway_genes"] = df["wikipathways_id"].map(pathway_to_genes).fillna("")
    else:
        df["pathway_genes"] = ""

    column_order = [
        "cnv", "locus", "chromosome", "start", "end", 
        "region_GRCh37", "region_GRCh38",
        "description", "pubmed_ids",
        "genes_hgnc_symbol", "genes_hgnc_name", "genes_hgnc_id", "genes_entrez_id",
        "genes_ensembl_id", "genes_uniprot_id", "wikipathways_id", "pathway_genes",
        "orphadata_orphacode", "orphadata_cause", "orphadata_definition",
        "orphadata_prevalence",
        "orphadata_phenotypes_obligate(100%)",
        "orphadata_phenotypes_very_frequent(99-80%)",
        "orphadata_phenotypes_frequent(79-30%)",
        "orphadata_phenotypes_occasional(29-5%)",
        "orphadata_phenotypes_very_rare(<4-1%)",
        "orphadata_phenotypes_excluded(0%)",
        "orphadata_hpo_id",
        "orphadata_omim_id", 
    ]

    # Make sure all expected columns exist
    for col in column_order:
        if col not in df.columns:
            df[col] = ""

    df = df[column_order]

    df.to_excel(output_dir / "CNVPathwayAtlas-data.xlsx", index=False)
    # df.to_parquet(output_dir / "CNVPathwayAtlas-data.parquet", index=False)
    
    # Build JSON
    cnv_json = {}
    for _, row in df.iterrows():
        cnv_name = row["cnv"]
        if cnv_name not in cnv_json:
            cnv_json[cnv_name] = {
                "cnv": cnv_name,
                "locus": row["locus"],
                "chromosome": row["chromosome"],
                "start": row["start"],
                "end": row["end"],
                "region_GRCh37": row["region_GRCh37"],
                "region_GRCh38": row["region_GRCh38"],
                "description": row["description"],
                "pubmed_ids": row["pubmed_ids"].split(";") if row["pubmed_ids"] else [],
                "wikipathways_id": row["wikipathways_id"],
                "pathway_genes": row["pathway_genes"].split(";") if row["pathway_genes"] else [],
                "region_genes": [],
                "orphadata": {}
            }
        
        # Add gene
        gene_symbol = row["genes_hgnc_symbol"]
        if gene_symbol:
            gene_entry = {
                "symbol": gene_symbol,
                "name": row["genes_hgnc_name"],
                "hgnc_id": row["genes_hgnc_id"],
                "entrez_id": row["genes_entrez_id"],
                "ensembl_id": row["genes_ensembl_id"],
                "uniprot_id": row["genes_uniprot_id"]
            }
            if gene_entry not in cnv_json[cnv_name]["region_genes"]:
                cnv_json[cnv_name]["region_genes"].append(gene_entry)
        
        # Add orphadata
        orphacode = row["orphadata_orphacode"]
        if orphacode and orphacode != "NA":
            if orphacode not in cnv_json[cnv_name]["orphadata"]:
                cnv_json[cnv_name]["orphadata"][orphacode] = {
                    "orphacode": orphacode,
                    "cause": row["orphadata_cause"],
                    "definition": row["orphadata_definition"],
                    "prevalence": row["orphadata_prevalence"],
                    "omim_ids": row["orphadata_omim_id"].split(";") if row["orphadata_omim_id"] else [],
                    "phenotypes": {
                        "obligate(100%)": [],
                        "very_frequent(99-80%)": [],
                        "frequent(79-30%)": [],
                        "occasional(29-5%)": [],
                        "very_rare(<4-1%)": [],
                        "excluded(0%)": []
                    }
                }
            
            # Add phenotypes to frequency category
            orpha = cnv_json[cnv_name]["orphadata"][orphacode]
            hpo_id = row["orphadata_hpo_id"] or None
            for cat, col in [
                ("obligate(100%)", "orphadata_phenotypes_obligate(100%)"),
                ("very_frequent(99-80%)", "orphadata_phenotypes_very_frequent(99-80%)"),
                ("frequent(79-30%)", "orphadata_phenotypes_frequent(79-30%)"),
                ("occasional(29-5%)", "orphadata_phenotypes_occasional(29-5%)"),
                ("very_rare(<4-1%)", "orphadata_phenotypes_very_rare(<4-1%)"),
                ("excluded(0%)", "orphadata_phenotypes_excluded(0%)")
            ]:
                pheno_name = row[col]
                if pheno_name:
                    pheno_entry = {"name": pheno_name, "hpo_id": hpo_id}
                    if pheno_entry not in orpha["phenotypes"][cat]:
                        orpha["phenotypes"][cat].append(pheno_entry)
    
    # Convert orphadata dict to list for each CNV
    for cnv_name in cnv_json:
        cnv_json[cnv_name]["orphadata"] = list(cnv_json[cnv_name]["orphadata"].values())
    
    import json
    
    def format_json_compact_arrays(data):
        """Format JSON with compact arrays for pathway_genes."""
        lines = []
        json_str = json.dumps(data, indent=2, default=str)
        
        import re
        def compact_array(match):
            arr_content = match.group(1)
            # Remove newlines and extra spaces
            items = re.findall(r'"([^"]*)"', arr_content)
            return '"pathway_genes": [' + ', '.join(f'"{item}"' for item in items) + ']'
        
        json_str = re.sub(
            r'"pathway_genes": \[\s*((?:"[^"]*",?\s*)+)\]',
            compact_array,
            json_str
        )
        return json_str
    
    with open(output_dir / "CNVPathwayAtlas-data.json", "w") as f:
        f.write(format_json_compact_arrays(list(cnv_json.values())))
    
    print("Exported: CNVPathwayAtlas-data.xlsx, and .json")

if __name__ == "__main__":
    main()
