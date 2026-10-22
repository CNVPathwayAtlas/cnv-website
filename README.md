# [CNVPathwayAtlas](https://cnvpathwayatlas.github.io/cnv-website/)

## Website
- [https://cnvpathwayatlas.github.io/cnv-website/](https://cnvpathwayatlas.github.io/cnv-website/)

## Data repository
- [https://github.com/CNVPathwayAtlas/cnv-data/](https://github.com/CNVPathwayAtlas/cnv-data)

## Licence
The content of this repository is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/) (see [LICENSE](LICENSE)).

## Citing
For citation details of our work and the data resources we used, refer to the [Documentation](https://cnvpathwayatlas.github.io/cnv-website/documentation/#how-to-cite).

## Download
The data files (XLSX, JSON and TSV) are listed in the [Documentation](https://cnvpathwayatlas.github.io/cnv-website/documentation/#data-files).

## How the website is built
The site uses Jekyll with the [Minimal Mistakes](https://github.com/mmistakes/minimal-mistakes) theme (`remote_theme`, version 4.26.2). Files in this repository with the same path as a theme file override the theme file.

The workflow [update-data.yml](.github/workflows/update-data.yml) runs when cnv-data releases a new data version. It runs these scripts and pushes the result:

| Script | Output |
|---|---|
| `scripts/build_yaml_files.py` | `_cnvs/*.md` (one page per CNV), `_data/data_version.yml`, `assets/pathways/*.svg`, `*.gpml` |
| `scripts/export_cnvs_to_table.py` | `assets/data/CNVPathwayAtlas-data.xlsx`, `.json`, `assets/data/tsv/*.tsv` |
| `scripts/export_jsonld.py` | `assets/data/CNVPathwayAtlas.jsonld`, `_data/jsonld/*.json` (schema.org/Bioschemas markup in each CNV page) |
| `scripts/generate-hpo-groups.py` | `assets/data/hpo_categories.json` |
| `scripts/generate_browser_data.py` | `assets/data/phenotype_browser_data.json` |

## Local build
```sh
git clone https://github.com/CNVPathwayAtlas/cnv-data.git ../cnv-data
python scripts/build_yaml_files.py ../cnv-data
python scripts/export_cnvs_to_table.py ../cnv-data
bundle install
bundle exec jekyll serve
```
