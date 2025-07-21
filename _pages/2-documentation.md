---
permalink: /documentation/
title: "Documentation"
toc: true
toc_label: "Table of Contents"
toc_sticky: true
---

This documentation provides detailed information on how we collected data and constructed molecular pathways, as well as how the data can be used for further analysis.

## What Are Rare CNVs

Copy number variants (CNVs) are structural genomic alterations involving DNA segments typically larger than 1 kilobase (kb). They contribute to human genetic diversity and have been implicated in various neurodevelopmental and neuropsychiatric disorders, including intellectual disability (ID), autism spectrum disorder (ASD), bipolar disorder (BD), and schizophrenia (SCZ). (<a href="https://pubmed.ncbi.nlm.nih.gov/16418744/" target="_blank">Feuk et al., 2006</a>; <a href="https://pubmed.ncbi.nlm.nih.gov/17122850/" target="_blank">Redon et al., 2006</a>; <a href="https://pubmed.ncbi.nlm.nih.gov/34504065/" target="_blank">Rees et al., 2021</a>)

<figure id="fig:cnv">
  <img src="/assets/images/cnv.png" alt="CNV representation" style="max-width:100%; height:auto;" />
  <figcaption><strong>Figure 1:</strong> Types of copy number variants (CNVs). Source: <a href="https://pubmed.ncbi.nlm.nih.gov/36737482/" target="_blank">Mollon et al., 2023</a>.</figcaption>
</figure>

## CNV Selection Criteria

We selected CNVs based on the availability of curated molecular pathways in the <a href="https://www.wikipathways.org/communities/rarediseases.html" target="_blank">WikiPathways Rare Diseases community</a>. In total, this resource includes 34 unique molecular pathways.

Most CNVs represented here are recurrent (i.e., involve the same genomic breakpoints) and are known to have a high prevalence among individuals with psychiatric disorders such as schizophrenia, as reported by <a href="https://pubmed.ncbi.nlm.nih.gov/27869829/" target="_blank">Marshall et al., 2017</a>. However, this resource is not limited to schizophrenia associated CNVs.

## Data Linked to Each CNV

Diseases associated with deletions or duplications in specific genomic regions were collected from established databases such as <a href="https://www.orphadata.com/" target="_blank">OrphaData</a> and <a href="https://omim.org/" target="_blank">OMIM</a>.
Each CNV was linked to these resources using their unique identifiers ORPHAcodes and OMIM IDs, respectively.  
When information was missing from these databases, we conducted literature research to supplement the data.

### Disease associated information
From OrphaData, we retrieved:
- Disease descriptions  
- Prevalence   

- Associated OMIM IDs  
- Phenotypic features labeled as *Very frequent (99–80%)*  

These phenotypic features were mapped to the [Human Phenotype Ontology (HPO)](https://hpo.jax.org/), providing structured and computable clinical data.

### Genes associated information
For gene level information, we queried the <a href="https://www.genenames.org/" target="_blank">HGNC</a> database to extract:
- Approved gene symbols  
- Gene names  
- Cross-references to external databases such as NCBI, Ensembl, and UniProt

<figure id="fig:data-flow">
  <img src="/assets/images/data_flow.png" alt="Data Flow Diagram" style="max-width:100%; height:auto;" />
  <figcaption><strong>Figure 2:</strong> Overview of the data collection and integration process.</figcaption>
</figure>

## Molecular Pathway Construction

*To be added.*  

## Further Analysis with Cytoscape

*To be added.*  

## How to Cite

How to cite
Licence, uncer which conditions to use it
