// Append the gene table making sure that the missing data from HGNC is properly handled 
// It is used in CNV pages. 

import { fetchGeneData } from './fetch-gene-data.js';

export async function displayGeneLinks(geneSymbols) {
    const tableBody = document.querySelector('#gene-info-table tbody');

    for (const symbol of geneSymbols) {
        const geneData = await fetchGeneData(symbol);
        const row = document.createElement('tr');

        if (geneData) {
            const hgncId = geneData.hgnc_id || 'No ID';
            const geneName = geneData.name || 'No name available';
            const ncbiId = geneData.entrez_id || 'No ID';
            const ensemblId = geneData.ensembl_gene_id || 'No ID';  
            const uniprotId = geneData.uniprot_ids ? geneData.uniprot_ids[0] : 'No ID';
            const omimId = geneData.omim_id || 'No ID';

            row.innerHTML = `
                <td><a href="https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/${hgncId}" target="_blank">${symbol}</a></td>
                <td>${geneName}</td>
                <td><a href="https://www.ncbi.nlm.nih.gov/gene/${ncbiId}" target="_blank">${ncbiId}</a></td>
                <td><a href="https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=${ensemblId}" target="_blank">${ensemblId}</a></td>
                <td><a href="https://www.uniprot.org/uniprotkb/${uniprotId}" target="_blank">${uniprotId}</a></td>
                <td><a href="https://omim.org/entry/${omimId}" target="_blank">${omimId}</a></td>
            `;
        } else {
            row.innerHTML = `<td colspan="7">No data available for ${symbol}</td>`;
        }

        tableBody.appendChild(row);
    }
}