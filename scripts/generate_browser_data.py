#!/usr/bin/env python3
"""
Generate the star-schema phenotype-genotype browser JSON from CNV markdown files.

Terminology:
  - location  : a genomic region (e.g. 22q11.21), keyed by cnv field in front matter
  - disorder   : a clinical disease linked to a location via orphacode (e.g. ORPHA:567)

Produces assets/data/phenotype_browser_data.json with:
  - locations  : array of genomic location records
  - disorders  : dict of disorder_id -> {id, name, location_id, cause, prevalence, definition}
  - phenotypes : dict of HPO_ID -> {label, disorder_entries: [{disorder_id, frequency, cause}]}
  - categories : dict of category_HPO_ID -> {label, phenotype_ids: [...]}
  - genes      : dict of symbol -> {name, location_ids: [...]}
"""

import json
import os
import glob
import re
import yaml
import urllib.request

CNVS_DIR = os.path.join(os.path.dirname(__file__), '..', '_cnvs')
HPO_CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'hpo_categories.json')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'assets', 'data', 'phenotype_browser_data.json')
WP_INFO_URL = "https://www.wikipathways.org/json/getPathwayInfo.json"


def fetch_wp_names():
    """Fetch WikiPathways name map {wpid: name} from the public json API."""
    try:
        print(f"Fetching WikiPathways names from {WP_INFO_URL} …")
        req = urllib.request.Request(
            WP_INFO_URL,
            headers={"User-Agent": "CNVPathwayAtlas-DataGen/1.0 (Python)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        result = {
            p['id']: p['name']
            for p in data.get('pathwayInfo', [])
            if p.get('id')
        }
        print(f"  Got {len(result)} pathway names")
        return result
    except Exception as e:
        print(f"  WARNING: could not fetch WP names ({e})")
        return {}


def parse_front_matter(filepath):
    """Parse YAML front matter from a markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        print(f"YAML error in {filepath}: {e}")
        return None


def disorder_name(orpha, location_id):
    """Derive a human-readable name for a disorder from its orpha entry."""
    cause = orpha.get('cause', '')
    # Fall back to "location cause syndrome"
    if cause:
        return f"{location_id} {cause} syndrome (ORPHA:{orpha.get('orphacode','')})"
    return f"{location_id} CNV disorder (ORPHA:{orpha.get('orphacode','')})"


def main():
    # Fetch WikiPathways names once
    wp_names = fetch_wp_names()

    # Load HPO categories mapping
    with open(HPO_CATEGORIES_FILE, 'r') as f:
        hpo_cat_data = json.load(f)

    categories_raw = hpo_cat_data.get('categories', {})
    phenotype_to_category = hpo_cat_data.get('phenotypeToCategory', {})

    # Data structures
    locations = []           # genomic location records
    disorders = {}           # disorder_id (ORPHA:xxx) -> disorder record
    phenotypes = {}          # hpo_id -> {label, disorder_entries: [{disorder_id, frequency, cause}]}
    genes = {}               # symbol -> {name, location_ids: set()}
    categories = {}          # cat_hpo_id -> {label, phenotype_ids: set()}

    # Initialize categories
    for cat_id, cat_info in categories_raw.items():
        categories[cat_id] = {
            'label': cat_info['label'],
            'phenotype_ids': set()
        }

    # Process each CNV markdown file
    md_files = sorted(glob.glob(os.path.join(CNVS_DIR, '*.md')))
    for filepath in md_files:
        fm = parse_front_matter(filepath)
        if not fm:
            continue

        cnv_name = os.path.basename(filepath).replace('.md', '')
        location_id = fm.get('cnv', fm.get('locus', cnv_name))

        location_record = {
            'id': location_id,
            'locus': fm.get('locus', ''),
            'chromosome': str(fm.get('chromosome', '')).strip("'"),
            'start': fm.get('start', 0),
            'end': fm.get('end', 0),
            'description': fm.get('description', ''),
            'url': f'/cnv/{cnv_name.replace(".", "-")}/',
            'gene_symbols': [],
            'gene_count': 0,
            'disorder_ids': [],   # list of ORPHA:xxx ids linked to this location
            'wikipathways_id': fm.get('wikipathways_id', '') or '',
            'pathway_name': wp_names.get(fm.get('wikipathways_id', '') or '', ''),
        }

        # Process genes
        if fm.get('genes'):
            for gene in fm['genes']:
                symbol = gene.get('symbol', '')
                if symbol:
                    location_record['gene_symbols'].append(symbol)
                    if symbol not in genes:
                        genes[symbol] = {
                            'name': gene.get('name', ''),
                            'location_ids': set()
                        }
                    genes[symbol]['location_ids'].add(location_id)
            location_record['gene_count'] = len(location_record['gene_symbols'])

        # Process orphadata — each entry is a distinct disorder
        orpha_list = [
            o
            for o in (fm.get("orphadata") or [])
            if str(o.get("orphacode", "")).strip()
        ]

        if orpha_list:
            for orpha in orpha_list:
                orphacode = str(orpha.get('orphacode', '')).strip()
                disorder_id = f"ORPHA:{orphacode}"
                cause = orpha.get('cause', '')
                name = disorder_name(orpha, location_id)

                disorder_record = {
                    'id': disorder_id,
                    'orphacode': orphacode,
                    'name': name,
                    'location_id': location_id,
                    'cause': cause,
                    'prevalence': orpha.get('prevalence', ''),
                    'definition': orpha.get('definition', '') or '',
                    'no_orphacode': False,
                }
                disorders[disorder_id] = disorder_record
                location_record['disorder_ids'].append(disorder_id)
        else:
            # No orphacode: create a local disorder entry by location id
            # TODO decide how (whether) to mint URIs for CNVPathwayAtlas
            disorder_id = f"LOC:{location_id}"
            disorder_record = {
                'id': disorder_id,
                'orphacode': '',
                'name': f"{location_id} CNV (no ORPHA code)",
                'location_id': location_id,
                'cause': '',
                'prevalence': '',
                'definition': '',
                'no_orphacode': True,
            }
            disorders[disorder_id] = disorder_record
            location_record['disorder_ids'].append(disorder_id)
            # use this synthetic id in all phenotype entries below
            orpha_list = [
                {
                    "orphacode": "",
                    "cause": "",
                    "phenotypes_obligate(100%)": fm.get("phenotypes_obligate(100%)", []) or [],
                    "phenotypes_very_frequent(99-80%)": fm.get("phenotypes_very_frequent(99-80%)", []) or [],
                    "phenotypes_frequent(79-30%)": fm.get("phenotypes_frequent(79-30%)", []) or [],
                    "phenotypes_occasional(29-5%)": fm.get("phenotypes_occasional(29-5%)", []) or [],
                    "phenotypes_very_rare(<4-1%)": fm.get("phenotypes_very_rare(<4-1%)", []) or [],
                    "phenotypes_excluded(0%)": fm.get("phenotypes_excluded(0%)", []) or [],
                }
            ]


        # Process phenotype entries for each orpha entry
        for orpha in orpha_list:
            orphacode = str(orpha.get('orphacode', '')).strip()
            orpha_disorder_id = f"ORPHA:{orphacode}" if orphacode else f"LOC:{location_id}"
            # LOC here is just a placeholder, decide CURIE for CNVPA
            orpha_cause = orpha.get('cause', '')

            freq_tiers = {
                'obligate(100%)':      orpha.get('phenotypes_obligate(100%)', []) or [],
                'very_frequent(99-80%)': orpha.get('phenotypes_very_frequent(99-80%)', []) or [],
                'frequent(79-30%)':      orpha.get('phenotypes_frequent(79-30%)', []) or [],
                'occasional(29-5%)':    orpha.get('phenotypes_occasional(29-5%)', []) or [],
                'very_rare(<4-1%)':     orpha.get('phenotypes_very_rare(<4-1%)', []) or [],
                'excluded(0%)':      orpha.get('phenotypes_excluded(0%)', []) or [],
            }

            for frequency, pheno_list in freq_tiers.items():
                for pheno in pheno_list:
                    hpo_id = pheno.get('hpo_id', '')
                    hpo_name = pheno.get('name', '')
                    if not hpo_id:
                        continue

                    if hpo_id not in phenotypes:
                        phenotypes[hpo_id] = {
                            'label': hpo_name,
                            'disorder_entries': []
                        }

                    phenotypes[hpo_id]['disorder_entries'].append({
                        'disorder_id': orpha_disorder_id,
                        'frequency': frequency,
                        'cause': orpha_cause,
                    })

                    # Map to category
                    cat_id = phenotype_to_category.get(hpo_id)
                    if cat_id and cat_id in categories:
                        categories[cat_id]['phenotype_ids'].add(hpo_id)

        locations.append(location_record)

    # Convert sets to sorted lists for JSON serialization
    for symbol in genes:
        genes[symbol]["location_ids"] = sorted(genes[symbol]["location_ids"])

    for cat_id in categories:
        categories[cat_id]["phenotype_ids"] = sorted(
            categories[cat_id]["phenotype_ids"]
        )

    # Remove empty categories
    categories = {k: v for k, v in categories.items() if v['phenotype_ids']}

    # Build output
    output = {
        'generated': __import__('datetime').datetime.now().isoformat(),
        'locations': locations,
        'disorders': disorders,
        'phenotypes': phenotypes,
        'categories': categories,
        'genes': genes,
        'stats': {
            'total_locations': len(locations),
            'total_disorders': len(disorders),
            'total_phenotypes': len(phenotypes),
            'total_genes': len(genes),
            'total_categories': len(categories),
        }
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Generated {OUTPUT_FILE}")
    print(f"  Locations : {len(locations)}")
    print(f"  Disorders : {len(disorders)}")
    print(f"  Phenotypes: {len(phenotypes)}")
    print(f"  Genes     : {len(genes)}")
    print(f"  Categories: {len(categories)}")


if __name__ == '__main__':
    main()
