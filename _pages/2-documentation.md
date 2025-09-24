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

Copy number variants (CNVs) are structural genomic alterations involving DNA segments typically larger than 1 kilobase (kb). They contribute to human genetic diversity and have been implicated in various neurodevelopmental and neuropsychiatric disorders, including intellectual disability (ID), autism spectrum disorder (ASD), bipolar disorder (BD), and schizophrenia (SCZ). (<a href="https://pubmed.ncbi.nlm.nih.gov/16418744/" target="_blank">Feuk et al., 2006</a>; <a href="https://pubmed.ncbi.nlm.nih.gov/17122850/" target="_blank">Redon et al., 2006</a>; <a href="https://pubmed.ncbi.nlm.nih.gov/34504065/" target="_blank">Rees et al., 2021</a>)

<figure id="fig:cnv">
  <img src="{{ site.baseurl }}/assets/images/cnv.png" alt="CNV representation" style="max-width:100%; height:auto;" />
  <figcaption><strong>Figure 1:</strong> Types of copy number variants (CNVs). Source: <a href="https://pubmed.ncbi.nlm.nih.gov/36737482/" target="_blank">Mollon et al., 2023</a>.</figcaption>
</figure>

# CNV selection criteria
We selected CNVs based on the availability of curated molecular pathways in the <a href="https://www.wikipathways.org/communities/rarediseases.html" target="_blank">WikiPathways Rare Diseases community</a>. In total, this resource includes 35 unique molecular pathways.

Most CNVs represented here are recurrent (i.e., involve the same genomic breakpoints) and are known to have a high prevalence among individuals with psychiatric disorders such as schizophrenia, as reported by <a href="https://pubmed.ncbi.nlm.nih.gov/27869829/" target="_blank">Marshall et al., 2017</a>. However, this resource is not limited to schizophrenia associated CNVs.

# Data linked to each CNV
Diseases associated with deletions or duplications in specific genomic regions were collected from established databases such as <a href="https://www.orphadata.com/" target="_blank">OrphaData</a> and <a href="https://omim.org/" target="_blank">OMIM</a>.
Each CNV was linked to these resources using their unique identifiers ORPHAcodes and OMIM IDs, respectively.  
When information was missing from these databases, we conducted literature research to supplement the data.

## Disease associated information
From OrphaData we retrieved:
- Disease descriptions  
- Prevalence   
- Associated OMIM IDs  
- Phenotypic features labeled as *Very frequent (99–80%)*  

These phenotypic features were mapped to the <a href="https://hpo.jax.org/" target="_blank">Human Phenotype Ontology (HPO)</a>, providing structured and computable clinical data.

## Genes associated information
For gene level information, we queried the <a href="https://www.genenames.org/" target="_blank">HGNC</a> database to extract:
- Approved gene symbols  
- Gene names  
- Cross-references to external databases such as NCBI, Ensembl, and UniProt

<figure id="fig:data-flow">
  <img src="{{ site.baseurl }}/assets/images/data_flow.png" alt="Data Flow Diagram" style="max-width:100%; height:auto;" />
  <figcaption><strong>Figure 2:</strong> Overview of the data collection and integration process.</figcaption>
</figure>

# Molecular pathway construction
To build molecular pathways we used <a href="https://pathvisio.org/" target="_blank">PathVisio</a> together with <a href="https://pathvisio.org/plugins/plugins-repo" target="_blank"> BridgeDb and WikiPathways plugins</a>.

If you are new to PathVisio, start by following this
<a href="https://academy.wikipathways.org/stages/walk-install-pv/" target="_blank">PathVisio setup tutorial</a> to install the software and required plugins.

Once set up, you can learn how to create your own pathway using the
<a href="https://academy.wikipathways.org/path.html" target="_blank">WikiPathways Academy</a>.

After creating your pathway, you can upload it to <a href="https://www.wikipathways.org/" target="_blank">WikiPathways</a> to share your knowledge with the community and even become a curator.

# Further analysis with Cytoscape
You can download the entire copy number variants table from the <a href="https://cnvpathwayatlas.github.io/cnv-website/" target="_blank">main page</a>.

| cnv | locus | chromosome | start | end | description | pubmed_id | genes_hgnc_symbol | genes_hgnc_name | genes_hgnc_id | genes_entrez_id | genes_ensembl_id | genes_uniprot_id | wikipathways_id | orphadata_orphacode | orphadata_cause | orphadata_definition | orphadata_prevalence | orphadata_phenotypes | orphadata_hpo_id | orphadata_omim_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1p36.33-p36.32 | 1p36.33-p36.32 | 1 | 0 | 2500000 | 1p36.33-p36.32 deletion or duplication... | - | OR4F5 | olfactory receptor... | HGNC:14825  | 79501 | ENSG00000186092 | Q8NH21 | WP5345 | 1606 | deletion | A rare chromosomal anomaly... | 15.0 (1–5 / 10 000)... | Pointed chin | HP:0000307 | 616975;607872 |

1. Open Cytoscape or download it from <a href="https://cytoscape.org/" target="_blank">cytoscape.org</a>
2. Go to **File → Import → Network from File**
3. Select your **CNV table** (e.g. all_cnvs_table.xlsx or a filtered version)
4. In the import dialog, set the appropriate columns:
   - one column as **Source Node** (e.g. `cnv`)
   - another as **Target Node** (e.g. `genes_hgnc_symbol`)
5. Click **OK** to import and view the network
6. **Extend the network** using the <a href="https://apps.cytoscape.org/apps/cytargetlinker" target="_blank">cytargetlinker app</a> with drug-, pathway-, or disease-related <a href="https://cytargetlinker.github.io/pages/linksets" target="_blank">linksets</a>

# Licence
This content is licensed under the <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank">Commons Attribution 4.0 International (CC BY 4.0) licence</a>. This means you are free to reuse the content in any way, including copying, distributing, displaying, or using it for commercial purposes, in any country or jurisdiction. The only requirement is that you give appropriate credit to us and to the original data sources we used (see citation guidelines below).

# How to cite
## How to cite our work
### CNV website
CNVPathwayAtlas: A comprehensive resource of Rare Copy Number Variants. Available on https://cnvpathwayatlas.github.io/cnv-website/ (accessed on date). 

### Data version 
You can cite the latest data version, or the specific version you used, from Zenodo:
<a href="https://doi.org/10.5281/zenodo.16319401" target="_blank"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.16319401.svg" alt="DOI"></a>

Example citation for Release v_2025-07-22 (Harvard style):
Alexandra Valeanu (2025) ‘CNVPathwayAtlas/cnv-data: Release v_2025-07-22’. Zenodo. doi: <a href="https://doi.org/10.5281/zenodo.16319401" target="_blank">10.5281/zenodo.16319401</a>. 

## How to cite external data sources
### Orphanet/Orphadata
Orphanet: an online rare disease and orphan drug data base. © INSERM 1999. Available on http://www.orpha.net. Accessed (accessed on date).

Orphadata: Free access data from Orphanet. © INSERM 1999. Available on https://www.orphadata.com. Data version (XML data version).

For further use of Orphadata, please consult their <a href="https://www.orphadata.com/legal-notice/" target="_blank">legal notice</a>.

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