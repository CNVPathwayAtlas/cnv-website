#!/usr/bin/env python3
"""
Generate HPO Categories File

This script extracts all HPO IDs from CNV files and fetches their
top-level categories from the OLS4 API, then saves them to a JSON file.

Run when new phenotypes are added:
    python scripts/generate-hpo-groups.py
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
import urllib.request
import urllib.parse

OLS4_BASE = 'https://www.ebi.ac.uk/ols4/api/ontologies/hp/terms'
SCRIPT_DIR = Path(__file__).parent
CNV_DIR = SCRIPT_DIR.parent / '_cnvs'
OUTPUT_FILE = SCRIPT_DIR.parent / 'assets' / 'data' / 'hpo_categories.json'

MAX_WORKERS = 10

EXCLUDED_ROOTS = {
    'HP:0000001',  # All
    'HP:0000118',  # Phenotypic abnormality
}

TOP_LEVEL_CATEGORIES = {
    'HP:0025354',  # Abnormal cellular phenotype
    'HP:0001871',  # Abnormality of blood and blood-forming tissues
    'HP:0000152',  # Abnormality of head or neck
    'HP:0040064',  # Abnormality of limbs
    'HP:0001939',  # Abnormality of metabolism/homeostasis
    'HP:0001197',  # Abnormality of prenatal development or birth
    'HP:0000769',  # Abnormality of the breast
    'HP:0001626',  # Abnormality of the cardiovascular system
    'HP:0025031',  # Abnormality of the digestive system
    'HP:0000598',  # Abnormality of the ear
    'HP:0000818',  # Abnormality of the endocrine system
    'HP:0000478',  # Abnormality of the eye
    'HP:0000119',  # Abnormality of the genitourinary system
    'HP:0002715',  # Abnormality of the immune system
    'HP:0001574',  # Abnormality of the integument
    'HP:0033127',  # Abnormality of the musculoskeletal system
    'HP:0000707',  # Abnormality of the nervous system
    'HP:0002086',  # Abnormality of the respiratory system
    'HP:0045027',  # Abnormality of the thoracic cavity
    'HP:0001608',  # Abnormality of the voice
    'HP:0025142',  # Constitutional symptom
    'HP:0001507',  # Growth abnormality
    'HP:0002664',  # Neoplasm
}

PREFERRED_CATEGORIES = {
    'HP:0025354', 'HP:0001871', 'HP:0000152', 'HP:0040064', 'HP:0001939',
    'HP:0001197', 'HP:0000769', 'HP:0001626', 'HP:0025031', 'HP:0000598',
    'HP:0000818', 'HP:0000478', 'HP:0000119', 'HP:0002715', 'HP:0001574',
    'HP:0033127', 'HP:0000707', 'HP:0002086', 'HP:0045027', 'HP:0001608',
    'HP:0001507',
}

# Thread-safe cache for parent lookups
parent_cache = {}
parent_cache_lock = Lock()


def hpo_id_to_iri(hpo_id):
    return f"http://purl.obolibrary.org/obo/{hpo_id.replace(':', '_')}"


def iri_to_hpo_id(iri):
    match = re.search(r'HP_(\d+)$', iri)
    return f"HP:{match.group(1)}" if match else None


def fetch_parents(hpo_id):
    # Check cache first
    with parent_cache_lock:
        if hpo_id in parent_cache:
            return parent_cache[hpo_id]

    iri = hpo_id_to_iri(hpo_id)
    encoded_iri = urllib.parse.quote(urllib.parse.quote(iri, safe=''), safe='')
    url = f"{OLS4_BASE}/{encoded_iri}/parents?lang=en"

    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        parents = []
        if '_embedded' in data and 'terms' in data['_embedded']:
            for term in data['_embedded']['terms']:
                parent_id = iri_to_hpo_id(term.get('iri', ''))
                if parent_id:
                    parents.append({
                        'id': parent_id,
                        'label': term.get('label', parent_id)
                    })

        # Cache the result
        with parent_cache_lock:
            parent_cache[hpo_id] = parents

        return parents
    except Exception as e:
        print(f"  Error fetching parents for {hpo_id}: {e}")
        return []


def find_top_level_category(hpo_id, visited=None):
    if visited is None:
        visited = set()

    if hpo_id in visited:
        return []
    visited.add(hpo_id)

    if hpo_id in TOP_LEVEL_CATEGORIES:
        parents = fetch_parents(hpo_id)
        label = parents[0]['label'] if parents else hpo_id
        return [{'id': hpo_id, 'label': label}]

    parents = fetch_parents(hpo_id)

    if not parents:
        return []

    all_categories = []
    for parent in parents:
        if parent['id'] in TOP_LEVEL_CATEGORIES:
            all_categories.append({'id': parent['id'], 'label': parent['label']})
        elif parent['id'] not in EXCLUDED_ROOTS:
            parent_categories = find_top_level_category(parent['id'], visited)
            all_categories.extend(parent_categories)

    return all_categories


def select_best_category(categories):
    if not categories:
        return None
    if len(categories) == 1:
        return categories[0]

    unique = []
    seen = set()
    for cat in categories:
        if cat['id'] not in seen:
            seen.add(cat['id'])
            unique.append(cat)

    if len(unique) == 1:
        return unique[0]

    preferred = [c for c in unique if c['id'] in PREFERRED_CATEGORIES]
    return preferred[0] if preferred else unique[0]


def process_hpo_id(hpo_id):
    """Process a single HPO ID and return (hpo_id, category)."""
    found_categories = find_top_level_category(hpo_id)
    best_category = select_best_category(found_categories)
    return hpo_id, best_category


def extract_hpo_ids(content):
    return set(re.findall(r'hpo_id:\s*(HP:\d+)', content))


def main():
    print('Extracting HPO IDs from CNV files...')

    all_hpo_ids = set()
    files = list(CNV_DIR.glob('*.md'))

    for file in files:
        content = file.read_text(encoding='utf-8')
        hpo_ids = extract_hpo_ids(content)
        all_hpo_ids.update(hpo_ids)

    print(f'Found {len(all_hpo_ids)} unique HPO IDs across {len(files)} files')

    categories = {}
    hpo_list = sorted(all_hpo_ids)
    total = len(hpo_list)

    print(f'Fetching categories with {MAX_WORKERS} concurrent workers...')

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_hpo_id, hpo_id): hpo_id for hpo_id in hpo_list}

        for i, future in enumerate(as_completed(futures), 1):
            hpo_id, category = future.result()
            categories[hpo_id] = category
            if i % 50 == 0 or i == total:
                print(f'  Progress: {i}/{total}')

    save_output(categories)
    print(f'\nDone! Total: {len(categories)} HPO IDs processed.')


def save_output(categories):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    # Build hierarchical structure: category_id -> {label, phenotypes: [...]}
    hierarchical = {}
    # Build lightweight lookup: phenotype_id -> category_id
    phenotype_to_category = {}

    for hpo_id, category in categories.items():
        if category is None:
            continue

        cat_id = category['id']
        cat_label = category['label']

        if cat_id not in hierarchical:
            hierarchical[cat_id] = {
                'label': cat_label,
                'phenotypes': []
            }

        hierarchical[cat_id]['phenotypes'].append(hpo_id)
        phenotype_to_category[hpo_id] = cat_id

    # Sort phenotypes within each category for consistency
    for cat in hierarchical.values():
        cat['phenotypes'].sort()

    output = {
        'generated': datetime.now().isoformat(),
        'version': 2,
        'categories': hierarchical,
        'phenotypeToCategory': phenotype_to_category
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
