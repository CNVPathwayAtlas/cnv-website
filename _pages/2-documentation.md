---
permalink: /documentation/
title: "Documentation"
toc: true
toc_label: "Contents"
toc_sticky: true
layout: single
---

This documentation provides detailed information on how we collected data and constructed molecular pathways, as well as how the data can be used for further analysis.

# What are rare CNVs

Copy number variants (CNVs) are structural genomic alterations involving DNA segments typically larger than 1 kilobase (kb). They contribute to human genetic diversity and have been implicated in various neurodevelopmental and neuropsychiatric disorders, including intellectual disability (ID), autism spectrum disorder (ASD), bipolar disorder (BD), and schizophrenia (SCZ). (<a href="https://pubmed.ncbi.nlm.nih.gov/16418744/" target="_blank" rel="noopener noreferrer">Feuk et al., 2006</a>; <a href="https://pubmed.ncbi.nlm.nih.gov/17122850/" target="_blank" rel="noopener noreferrer">Redon et al., 2006</a>; <a href="https://pubmed.ncbi.nlm.nih.gov/34504065/" target="_blank" rel="noopener noreferrer">Rees et al., 2021</a>)

<figure id="fig:cnv">
  <img src="{{ site.baseurl }}/assets/images/cnv.png" alt="CNV representation" style="max-width:50%; height:auto;" />
  <figcaption><strong>Figure 1:</strong> Types of copy number variants (CNVs). Modified figure from: <a href="https://pubmed.ncbi.nlm.nih.gov/36737482/" target="_blank" rel="noopener noreferrer">Mollon et al., 2023</a>.</figcaption>
</figure>

# CNV selection criteria
We selected CNVs based on the availability of curated molecular pathways in the <a href="https://www.wikipathways.org/communities/rarediseases.html" target="_blank" rel="noopener noreferrer">WikiPathways Rare Diseases community</a>. In total, this resource includes 38 unique molecular pathways.

Most CNVs represented here are recurrent (i.e., involve the same genomic breakpoints) and are known to have a high prevalence among individuals with psychiatric disorders such as schizophrenia, as reported by <a href="https://pubmed.ncbi.nlm.nih.gov/27869829/" target="_blank" rel="noopener noreferrer">Marshall et al., 2017</a>. However, this resource is not limited to schizophrenia associated CNVs.

# Data linked to each CNV
Diseases associated with deletions or duplications in specific genomic regions were collected from established databases such as <a href="https://www.orphadata.com/" target="_blank" rel="noopener noreferrer">OrphaData</a> and <a href="https://omim.org/" target="_blank" rel="noopener noreferrer">OMIM</a>.
Each CNV was linked to these resources using their unique identifiers ORPHAcodes and OMIM IDs, respectively.  
When information was missing from these databases, we conducted literature research to supplement the data.

## Disease associated information
From OrphaData we retrieved:
- Disease descriptions  
- Prevalence   
- Associated OMIM IDs  
- Phenotypic features labeled as obligate (100%), very frequent (99%-80%), frequent (79%-30%), occasional (29%-5%), very rare (<4-1%), and excluded (0%).

These phenotypic features were mapped to the <a href="https://hpo.jax.org/" target="_blank" rel="noopener noreferrer">Human Phenotype Ontology (HPO)</a>, providing structured clinical data.

## Genes associated information
For gene level information, we queried the <a href="https://www.genenames.org/" target="_blank" rel="noopener noreferrer">HGNC</a> database to extract:
- Approved gene symbols  
- Gene names  
- Cross-references to external databases such as NCBI, Ensembl, and UniProt

<figure id="fig:data-flow">
  <img src="{{ site.baseurl }}/assets/images/data_flow.png" alt="Data Flow Diagram" style="max-width:100%; height:auto;" />
  <figcaption><strong>Figure 2:</strong> Overview of the data collection and integration process.</figcaption>
</figure>

# Molecular pathway construction
To build molecular pathways we used <a href="https://pathvisio.org/" target="_blank" rel="noopener noreferrer">PathVisio</a> together with <a href="https://pathvisio.org/plugins/plugins-repo" target="_blank" rel="noopener noreferrer"> BridgeDb and WikiPathways plugins</a>.

If you are new to PathVisio, start by following this
<a href="https://academy.wikipathways.org/stages/walk-install-pv/" target="_blank" rel="noopener noreferrer">PathVisio setup tutorial</a> to install the software and required plugins.

Once set up, you can learn how to create your own pathway using the
<a href="https://academy.wikipathways.org/path.html" target="_blank" rel="noopener noreferrer">WikiPathways Academy</a>.

After creating your pathway, you can upload it to <a href="https://www.wikipathways.org/" target="_blank" rel="noopener noreferrer">WikiPathways</a> to share your knowledge with the community and even become a curator.

# Genome coordinates
Each CNV has a region in two genome builds: GRCh37 (hg19) and GRCh38 (hg38). GRCh37 is the main build: the CNVs Explorer, the genome overview, the Phenotype Browser and the region size use GRCh37. The GRCh38 region is given as additional information. The genome browser on each CNV page opens in GRCh37 and can show GRCh38.

# Data updates
The data is kept in the <a href="https://github.com/CNVPathwayAtlas/cnv-data" target="_blank" rel="noopener noreferrer">cnv-data</a> repository. Every week an automatic job checks Orphadata, HGNC and WikiPathways for new releases. When a source release or the curated input changes the processed data, a new data version (`v_<date>`) is released and this website is updated. The current data version and the source release dates are shown at the bottom of each page.

Gene symbols in the curated input are mapped to the approved HGNC symbol. When HGNC changed a symbol, the CNV page shows the approved symbol and the earlier symbol (for example "FIMP1, was C16orf92").

The molecular pathway on each CNV page is the WikiPathways SVG of the pathway revision in the data version. The GPML file can be downloaded from the same section. Genes in the CNV region that are also in the pathway are marked in the gene table.

# Uploading a new CNV
You can use our <a href="{{ '/contact/' | relative_url }}">contact forms</a> if you want to request a new CNV or you want to report an error.

If you are already part of the CNVPathwayAtlas team and want to add a new CNV:
- make your CNV pathway and upload it to WikiPathways
- add the CNV to `data/input/cnv_data.tsv` in <a href="https://github.com/CNVPathwayAtlas/cnv-data" target="_blank" rel="noopener noreferrer">cnv-data</a> (see its README for the columns)

# Data files
All files are licensed under CC BY 4.0.

| File | Content |
|---|---|
| <a href="{{ '/assets/data/CNVPathwayAtlas-data.xlsx' | relative_url }}">CNVPathwayAtlas-data.xlsx</a> | All data in one table: one row per CNV, gene, disorder and phenotype (columns below) |
| <a href="{{ '/assets/data/CNVPathwayAtlas-data.json' | relative_url }}">CNVPathwayAtlas-data.json</a> | One record per CNV |
| <a href="{{ '/assets/data/CNVPathwayAtlas.jsonld' | relative_url }}">CNVPathwayAtlas.jsonld</a> | Linked data (JSON-LD) with <a href="https://schema.org/">schema.org</a> and <a href="https://bioschemas.org/">Bioschemas</a> types: CNV as `BioChemEntity` (Sequence Ontology `SO:0001019`), genes as `Gene` (HGNC), Orphanet disorders as `MedicalCondition` (ORDO), HPO phenotypes as `MedicalSignOrSymptom` with the Orphanet frequency class, pathways and PubMed articles as `subjectOf`. Each CNV page also contains its part of this graph. Excluded (0%) phenotypes are not in the graph |
| <a href="{{ '/assets/data/tsv/cnvs.tsv' | relative_url }}">tsv/cnvs.tsv</a> | One row per CNV: regions (GRCh37, GRCh38), size, CNV types, ORPHAcodes, pathway, gene counts, PubMed IDs, description |
| <a href="{{ '/assets/data/tsv/cnv_genes.tsv' | relative_url }}">tsv/cnv_genes.tsv</a> | One row per CNV and gene: approved HGNC symbol, symbol in the input, HGNC, NCBI Gene, Ensembl, UniProt and OMIM IDs, locus group, in pathway |
| <a href="{{ '/assets/data/tsv/cnv_disorders.tsv' | relative_url }}">tsv/cnv_disorders.tsv</a> | One row per CNV and Orphanet disorder: ORPHAcode, name, cause, CNV type, prevalence, OMIM IDs, definition |
| <a href="{{ '/assets/data/tsv/disorder_phenotypes.tsv' | relative_url }}">tsv/disorder_phenotypes.tsv</a> | One row per disorder and HPO phenotype, with the Orphanet frequency class |
| <a href="{{ '/assets/data/tsv/pathway_genes.tsv' | relative_url }}">tsv/pathway_genes.tsv</a> | One row per gene node in each WikiPathways pathway, with the GPML xref and the mapped HGNC gene (`mapped_by`: `xref`, or `label` when the label is an approved HGNC symbol) |

# Further analysis with Cytoscape
You can download the entire copy number variants table from the <a href="{{ '/' | relative_url }}">main page</a>.

| cnv | locus | chromosome | start | end | region_GRCh37 | region_GRCh38 | description | pubmed_ids | genes_hgnc_symbol | genes_hgnc_name | genes_hgnc_id | genes_entrez_id | genes_ensembl_id | genes_uniprot_id | wikipathways_id | pathway_genes | orphadata_orphacode | orphadata_cause | orphadata_definition | orphadata_prevalence | orphadata_phenotypes_obligate(100%) | orphadata_phenotypes_very_frequent(99-80%) | orphadata_phenotypes_frequent(79-30%) | orphadata_phenotypes_occasional(29-5%) | orphadata_phenotypes_very_rare(<4-1%) | orphadata_phenotypes_excluded(0%) | orphadata_hpo_id | orphadata_omim_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2q37.3 | 2q37.3 | 2 | 239716679 | 243199373 | Chr2:239716679-243199373 | Chr2:238808038-241873823 | The 2q37 copy number variation syndrome can result in the loss of up to 78 protein-coding genes. Patients with 2q37 CNV syndrome have intellectual disability, facial dysmorphism and skeletal and digit malformations. ... | 20691407;19752160;... | TWIST2 | twist family bHLH transcription factor 2 | HGNC:20670 | 117581 | ENSG00000233608 | Q8WVJ9 | WP5224 | ABCA1;ACKR3;...;USP40 | 1001 | microdeletion | A rare chromosomal anomaly involving deletion of chromosome band 2q37 and characterized by a broad spectrum of clinical findings including developmental delay, obesity, facial dysmorphism, and skeletal findings. ... | <1 / 1 000 000 |  | Round face |  |  |  |  | HP:0000311 | 600430 |

1. Open Cytoscape or download it from <a href="https://cytoscape.org/" target="_blank" rel="noopener noreferrer">cytoscape.org</a>
2. Go to **File → Import → Network from File**
3. Select your **CNV table** (e.g. CNVPathwayAtlas-data.xlsx or a filtered version)
4. In the import dialog, set the appropriate columns:
   - one column as **Source Node** (e.g. `cnv`)
   - another as **Target Node** (e.g. `genes_hgnc_symbol`)
5. Click **OK** to import and view the network
6. **Extend the network** using the <a href="https://apps.cytoscape.org/apps/cytargetlinker" target="_blank" rel="noopener noreferrer">cytargetlinker app</a> with drug-, pathway-, or disease-related <a href="https://cytargetlinker.github.io/pages/linksets" target="_blank" rel="noopener noreferrer">linksets</a>

You can also do the analysis programmatically using Python or R. For Python code, see the usecase repository <a href="https://github.com/CNVPathwayAtlas/cnv-usecase" target="_blank" rel="noopener noreferrer">CNVPathwayAtlas/cnv-usecase</a>.

# Licence
This content is licensed under the <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer">Creative Commons Attribution 4.0 International (CC BY 4.0) licence</a>. This means you are free to reuse the content in any way, including copying, distributing, displaying, or using it for commercial purposes, in any country or jurisdiction. The only requirement is that you give appropriate credit to us and to the original data sources we used (see citation guidelines below).

# How to cite
## How to cite our work
### CNVPathwayAtlas website
Valeanu, A., Duan, Y., Acosta, J.M., de Kok, T.M., van Amelsvoort, T. and Ehrhart, F., 2026. A dataset of rare copy number variants associated with neurodevelopmental and neuropsychiatric disorders. Scientific Data.

### Data version 
You can cite the latest release from Zenodo:
- doi: <a href="https://doi.org/10.5281/zenodo.17226746" target="_blank" rel="noopener noreferrer">10.5281/zenodo.17226746</a>. 

If you want to cite a specific release, e.g. Release v_2025-09-29 (Harvard style):
- Alexandra Valeanu (2025) ‘CNVPathwayAtlas/cnv-data: Release v_2025-09-29’. Zenodo. doi: <a href="https://doi.org/10.5281/zenodo.17226747" target="_blank" rel="noopener noreferrer">10.5281/zenodo.17226747</a>. 

## How to cite external data sources
### Orphanet/Orphadata
Orphanet: an online rare disease and orphan drug data base. © INSERM 1999. Available on http://www.orpha.net. Accessed (accessed on date).

Orphadata: Free access data from Orphanet. © INSERM 1999. Available on https://www.orphadata.com. Data version (XML data version).

For further use of Orphadata, please consult their <a href="https://www.orphadata.com/legal-notice/" target="_blank" rel="noopener noreferrer">legal notice</a>.

### HGNC
<cite>Genenames.org: the HGNC resources in 2023</cite>
<a href="https://orcid.org/0000-0002-7545-6817">Ruth L Seal</a>,
<a href="https://orcid.org/0000-0002-5269-0985">Bryony Braschi</a>,
<a href="https://orcid.org/0000-0002-7035-7107">Kristian Gray</a>,
<a href="https://orcid.org/0000-0002-0027-0858">Tamsin E M Jones</a>,
<a href="https://orcid.org/0000-0003-1818-8243">Susan Tweedie</a>,
<a href="http://orcid.org/0000-0002-0027-0858">Liora Haim-Vilmovsky</a>,
<a href="https://orcid.org/0000-0002-8380-5247">Elspeth A Bruford</a>
Nucleic Acids Research (Database issue)
<a href="https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkac888/6761747" class="paper-link">NAR</a> | <a href="http://europepmc.org/article/MED/36243972" class="paper-link">EuropePMC</a> | <a href="https://pubmed.ncbi.nlm.nih.gov/36243972/" class="paper-link">PubMed</a>

# Disclaimer
We are not affiliated with Orphanet or HGNC. We did not modify the data from Orphanet and HGNC. <br>

The content in this resource is provided for informational and research purposes only and is not intended as  medical, legal, or professional advice. The information presented here is offered for improving the understanding of rare copy number variation syndromes. <br>

Every effort has been made to ensure the accuracy and usefulness of the information contained in this resource. However, the authors do not claim any liability arising from the use or misuse of this material. Use of the content is at the user's own discretion and risk. <br>