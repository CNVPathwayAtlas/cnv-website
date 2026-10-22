"""Export the CNV pages (_cnvs/*.md) as JSON-LD with schema.org and Bioschemas types.

Writes:
- assets/data/CNVPathwayAtlas.jsonld: the full graph (Dataset and all CNVs)
- _data/jsonld/<page slug>.json: one CNV, embedded in its page as Bioschemas markup

Model:
- CNV: BioChemEntity, additionalType SO:0001019 (copy_number_variation)
- genes in the region: Gene (hasBioChemEntityPart), identified by HGNC
- Orphanet disorders: MedicalCondition (associatedDisease), identified by ORDO
- HPO phenotypes: MedicalSignOrSymptom (signOrSymptom), with the Orphanet frequency class
- pathway and PubMed evidence: CreativeWork / ScholarlyArticle (subjectOf)
"""
import json
import re
from pathlib import Path

import yaml

SITE_DIR = Path(__file__).resolve().parent.parent
CNVS_DIR = SITE_DIR / "_cnvs"
GRAPH_OUT = SITE_DIR / "assets" / "data" / "CNVPathwayAtlas.jsonld"
PAGES_OUT = SITE_DIR / "_data" / "jsonld"

CONFIG = yaml.safe_load((SITE_DIR / "_config.yml").read_text())
SITE_URL = CONFIG["url"].rstrip("/") + CONFIG["baseurl"]
DATASET_ID = SITE_URL + "/"

CONTEXT = {
    "@vocab": "https://schema.org/",
    "dct": "http://purl.org/dc/terms/",
}
CONFORMS_TO = {
    "BioChemEntity": "https://bioschemas.org/profiles/BioChemEntity/0.7-RELEASE-2019_06_19",
    "Gene": "https://bioschemas.org/profiles/Gene/1.0-RELEASE",
    "Dataset": "https://bioschemas.org/profiles/Dataset/1.0-RELEASE",
}

# Orphanet frequency classes; "excluded" (0%) is not a sign or symptom of the disorder
FREQUENCIES = {
    "obligate(100%)": "Obligate (100%)",
    "very_frequent(99-80%)": "Very frequent (99-80%)",
    "frequent(79-30%)": "Frequent (79-30%)",
    "occasional(29-5%)": "Occasional (29-5%)",
    "very_rare(<4-1%)": "Very rare (<4-1%)",
}


def slug(name):
    """Return the Jekyll default slug, the same as the /cnv/:name/ permalink."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def property_value(name, value):
    return {"@type": "PropertyValue", "name": name, "value": value}


def gene_node(gene):
    node = {
        "@type": "Gene",
        "dct:conformsTo": {"@id": CONFORMS_TO["Gene"]},
        "name": gene["symbol"],
    }
    if gene.get("hgnc_id"):
        node["@id"] = "https://identifiers.org/" + gene["hgnc_id"].lower()
        node["identifier"] = gene["hgnc_id"]
        node["url"] = "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/" + gene["hgnc_id"]
    if gene.get("name"):
        node["description"] = gene["name"]
    if gene.get("input_symbol"):
        node["alternateName"] = gene["input_symbol"]
    same_as = []
    if gene.get("entrez_id"):
        same_as.append("https://identifiers.org/ncbigene:" + gene["entrez_id"])
    if gene.get("ensembl_id"):
        same_as.append("https://identifiers.org/ensembl:" + gene["ensembl_id"])
    if gene.get("uniprot_id"):
        same_as.append("https://identifiers.org/uniprot:" + gene["uniprot_id"])
    if gene.get("omim_id"):
        same_as.append("https://identifiers.org/mim:" + gene["omim_id"])
    if same_as:
        node["sameAs"] = same_as
    return node


def condition_node(orpha):
    code = orpha["orphacode"]
    node = {
        "@type": "MedicalCondition",
        "@id": f"http://www.orpha.net/ORDO/Orphanet_{code}",
        "identifier": f"ORPHA:{code}",
        "url": f"https://www.orpha.net/en/disease/detail/{code}",
        "code": {"@type": "MedicalCode", "codeValue": code, "codingSystem": "ORPHA"},
    }
    if orpha.get("name"):
        node["name"] = orpha["name"]
    if orpha.get("definition"):
        node["description"] = orpha["definition"]
    if orpha.get("omim"):
        node["sameAs"] = ["https://identifiers.org/mim:" + omim for omim in orpha["omim"]]
    properties = []
    if orpha.get("cause"):
        properties.append(property_value("CNV cause", orpha["cause"]))
    if orpha.get("prevalence"):
        properties.append(property_value("Orphanet prevalence class", orpha["prevalence"]))
    if properties:
        node["additionalProperty"] = properties
    signs = []
    for key, label in FREQUENCIES.items():
        for phenotype in orpha.get(f"phenotypes_{key}", []):
            if not phenotype.get("hpo_id"):
                continue
            signs.append({
                "@type": "MedicalSignOrSymptom",
                "name": phenotype["name"],
                "code": {"@type": "MedicalCode", "codeValue": phenotype["hpo_id"], "codingSystem": "HPO"},
                "sameAs": "http://purl.obolibrary.org/obo/" + phenotype["hpo_id"].replace(":", "_"),
                "additionalProperty": property_value("Orphanet frequency", label),
            })
    if signs:
        node["signOrSymptom"] = signs
    return node


def cnv_node(page):
    node = {
        "@type": "BioChemEntity",
        "@id": f"{SITE_URL}/cnv/{slug(page['cnv'])}/",
        "dct:conformsTo": {"@id": CONFORMS_TO["BioChemEntity"]},
        "additionalType": "http://purl.obolibrary.org/obo/SO_0001019",
        "identifier": page["cnv"],
        "name": page["title"],
        "url": f"{SITE_URL}/cnv/{slug(page['cnv'])}/",
        "isPartOf": {"@id": DATASET_ID},
        "additionalProperty": [
            property_value("Cytogenetic location", page["locus"]),
            property_value("Region GRCh37", page["region_hg19"]),
            property_value("Region GRCh38", page["region_hg38"]),
        ],
    }
    if page.get("description"):
        node["description"] = page["description"]
    if page.get("genes"):
        node["hasBioChemEntityPart"] = [gene_node(g) for g in page["genes"]]
    if page.get("orphadata"):
        node["associatedDisease"] = [condition_node(o) for o in page["orphadata"]]
    subject_of = []
    if page.get("wikipathways_id"):
        wp = page["wikipathways_id"]
        subject_of.append({
            "@type": "CreativeWork",
            "@id": f"https://identifiers.org/wikipathways:{wp}",
            "identifier": wp,
            "name": page.get("pathway_name") or wp,
            "url": f"https://www.wikipathways.org/pathways/{wp}.html",
        })
    for pmid in page.get("pubmed_ids", []):
        subject_of.append({
            "@type": "ScholarlyArticle",
            "@id": f"https://identifiers.org/pubmed:{pmid}",
            "identifier": f"PMID:{pmid}",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    if subject_of:
        node["subjectOf"] = subject_of
    return node


def dataset_node(cnv_ids, version):
    return {
        "@type": "Dataset",
        "@id": DATASET_ID,
        "dct:conformsTo": {"@id": CONFORMS_TO["Dataset"]},
        "name": CONFIG["title"],
        "description": CONFIG["description"],
        "url": DATASET_ID,
        "version": version,
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "keywords": ["copy number variation", "rare diseases", "Orphanet", "Human Phenotype Ontology",
                     "WikiPathways", "HGNC"],
        "isBasedOn": ["https://www.orphadata.com/", "https://www.genenames.org/", "https://www.wikipathways.org/"],
        "distribution": {"@type": "DataDownload", "encodingFormat": "application/ld+json",
                         "contentUrl": f"{SITE_URL}/assets/data/CNVPathwayAtlas.jsonld"},
        "hasPart": [{"@id": cnv_id} for cnv_id in cnv_ids],
    }


def main():
    pages = [yaml.safe_load(p.read_text(encoding="utf-8").split("---\n")[1]) for p in sorted(CNVS_DIR.glob("*.md"))]
    nodes = [cnv_node(page) for page in pages]
    version = pages[0]["data_version"] if pages else ""

    graph = {"@context": CONTEXT, "@graph": [dataset_node([n["@id"] for n in nodes], version), *nodes]}
    GRAPH_OUT.write_text(json.dumps(graph, indent=1, ensure_ascii=False) + "\n")

    PAGES_OUT.mkdir(parents=True, exist_ok=True)
    for old in PAGES_OUT.glob("*.json"):
        old.unlink()
    for page, node in zip(pages, nodes):
        (PAGES_OUT / f"{slug(page['cnv'])}.json").write_text(
            json.dumps({"@context": CONTEXT, **node}, ensure_ascii=False) + "\n")

    print(f"JSON-LD: {len(nodes)} CNVs written to {GRAPH_OUT.name} and {PAGES_OUT}")


if __name__ == "__main__":
    main()
