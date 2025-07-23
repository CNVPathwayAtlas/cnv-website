import pandas as pd
from pathlib import Path
import yaml
import re
from typing import Optional, Tuple, List, Dict, Any


def get_latest_csv(dir_path: Path, pattern: str) -> Path:
    files = sorted(dir_path.glob(pattern), reverse=True)
    if not files:
        raise FileNotFoundError(f"No files matching {pattern} found in {dir_path}")
    return files[0]


def parse_region(region_str: Optional[str]) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    if not region_str:
        return None, None, None
    m = re.match(r"[cC]hr(\d+|[XYxy]):(\d+)-(\d+)", region_str)
    if not m:
        return None, None, None
    chrom = m.group(1).upper()
    start, end = int(m.group(2)), int(m.group(3))
    return chrom, start, end


def clean_gene_list(genes_str: Optional[str]) -> List[str]:
    if not isinstance(genes_str, str) or not genes_str.strip():
        return []
    clean_str = re.sub(r"<.*?>", "", genes_str)
    # split on ; or , or whitespace
    genes = [g.strip() for g in re.split(r"[;,]\s*|\s+", clean_str) if g.strip()]
    return genes


def nan_to_none(df: pd.DataFrame) -> pd.DataFrame:
    return df.where(pd.notnull(df), None)


def parse_phenotypes(phenotypes_str: Optional[str]) -> List[Dict[str, Optional[str]]]:
    if not phenotypes_str:
        return []
    phenotype_list = []
    for part in phenotypes_str.split(";"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(.+?)\s*\(?HP:(\d{7})\)?", part)
        if m:
            phenotype_list.append({"name": m.group(1).strip(), "hpo_id": f"HP:{m.group(2)}"})
        else:
            phenotype_list.append({"name": part, "hpo_id": None})
    return phenotype_list


def build_hgnc_dict(df_hgnc: pd.DataFrame) -> Dict[str, Dict[str, Optional[str]]]:
    hgnc_dict = {}
    for _, row in df_hgnc.iterrows():
        sym = row.get("symbol") or row.get("hgnc_symbol")
        if sym:
            hgnc_dict[sym] = {
                "name": row.get("name"),
                "hgnc_id": row.get("hgnc_id"),
                "entrez_id": row.get("entrez_id"),
                "ensembl_id": row.get("ensembl_gene_id"),
                "uniprot_id": row.get("uniprot_ids"),
            }
    return hgnc_dict


def build_orpha_dict(df_orpha: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    orpha_dict = {}
    for _, row in df_orpha.iterrows():
        code = str(row.get("OrphaCode", "")).strip()
        if not code:
            continue
        omim_raw = row.get("OMIM") or ""
        omim_list = [o.strip() for o in omim_raw.split(";") if o.strip()] if omim_raw else []
        orpha_dict[code] = {
            "definition": row.get("Definition"),
            "phenotypes": row.get("Phenotypes"),
            "prevalence": row.get("Prevalence"),
            "omim": omim_list,
            "pubmed_ids": [],  # TODO populate with actual PubMed IDs from orphadata
        }
    return orpha_dict


def parse_orphacodes(orphacodes_str: str, orpha_dict: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not orphacodes_str.strip():
        return []
    orphacodes_list = []
    entries = [e.strip() for e in re.split(r"[;,]", orphacodes_str) if e.strip()]
    for entry in entries:
        m = re.match(r"(\d+)(?:\(([^)]+)\))?", entry)
        if not m:
            continue
        code, cause = m.group(1), m.group(2) if m.group(2) else None
        orpha_info = orpha_dict.get(code, {})
        orphacodes_list.append({
            "orphacode": code,
            "cause": cause,
            "definition": orpha_info.get("definition"),
            "prevalence": orpha_info.get("prevalence"),
            "phenotypes": parse_phenotypes(orpha_info.get("phenotypes")),
            "omim": orpha_info.get("omim"),
            "pubmed_ids": orpha_info.get("pubmed_ids", []),
        })
    return orphacodes_list


def write_yaml_file(path: Path, yaml_dict: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(yaml_dict, f, sort_keys=False, allow_unicode=True)
        f.write("---\n")


def main() -> None:
    input_dir = Path("cnv-data/data/input")
    latest_dir = Path("cnv-data/data/latest")
    output_path = Path("_cnvs")
    output_path.mkdir(exist_ok=True)

    print(f"Looking for latest HGNC CSV in: {latest_dir}")
    hgnc_csv = get_latest_csv(latest_dir, "hgnc_filtered_*.csv")
    print(f"Found HGNC CSV: {hgnc_csv}")

    print(f"Looking for latest Orphadata CSV in: {latest_dir}")
    orpha_csv = get_latest_csv(latest_dir, "orphadata_filtered_*.csv")
    print(f"Found Orphadata CSV: {orpha_csv}")

    cnv_input = input_dir / "cnv_data.xlsx"

    print("Loading data...")
    df_cnv = nan_to_none(pd.read_excel(cnv_input))
    df_hgnc = nan_to_none(pd.read_csv(hgnc_csv, sep="\t", dtype=str))
    df_orpha = nan_to_none(pd.read_csv(orpha_csv, dtype=str, encoding="utf-8", quotechar='"'))

    print("Building lookup dictionaries...")
    hgnc_dict = build_hgnc_dict(df_hgnc)
    orpha_dict = build_orpha_dict(df_orpha)

    cnv_nr = 0

    for idx, row in df_cnv.iterrows():
        locus = row.get("locus") or f"cnv_{idx}"
        extra = str(row.get("extra") or "").strip()
        region = row.get("region") or ""
        chrom, start, end = parse_region(region)
        description = row.get("Description")
        wikipathways_id = row.get("WikiPathway ID")

        cnv_name = f"{locus}-{extra} Copy Number Variation Syndrome" if extra else f"{locus} Copy Number Variation Syndrome"

        genes = clean_gene_list(row.get("genes"))
        genes_info = [
            {**{"symbol": g}, **hgnc_dict.get(g, {"name": None, "hgnc_id": None, "entrez_id": None, "ensembl_id": None, "uniprot_id": None})}
            for g in genes
        ]

        orphacodes_list = parse_orphacodes(str(row.get("Orphacodes") or ""), orpha_dict)

        yaml_dict = {
            "layout": "cnv-page",
            "title": cnv_name,
            "cnv": f"{locus}-{extra}" if extra else locus,
            "locus": locus,
            "chromosome": chrom,
            "start": start,
            "end": end,
            "cytoband": f"/assets/images/cytoband/{locus}-{extra}.png" if extra else f"/assets/images/cytoband/{locus}.png",
            "description": description,
            "pubmed_ids": [],
            "genes": genes_info,
            "wikipathways_id": wikipathways_id,
            "orphadata": orphacodes_list,
        }

        raw_name = f"{locus}-{extra}" if extra else locus
        filename = re.sub(r"[:\s]", "", raw_name)
        yaml_filename = output_path / f"{filename}.md"

        write_yaml_file(yaml_filename, yaml_dict)
        cnv_nr += 1
        print(f"Written {yaml_filename.name}")

    print(f"{cnv_nr} YAML files created in {output_path}")


if __name__ == "__main__":
    main()