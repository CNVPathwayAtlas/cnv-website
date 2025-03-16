// Function to query the HGNC data for the respective gene - it is used in assets/js/populate-gene-table.js
// It uses the genes from the CNV pages

export async function fetchGeneData(geneSymbol) {
    try {
        const response = await fetch(`https://rest.genenames.org/fetch/symbol/${geneSymbol}`, {
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            console.error(`Failed to fetch data for ${geneSymbol}`);
            return null;
        }

        const data = await response.json();
        if (data.response && data.response.docs.length > 0) {
            return data.response.docs[0]; 
        } else {
            console.warn(`No data found for ${geneSymbol}`);
            return null;
        }
    } catch (error) {
        console.error('Error fetching gene data:', error);
        return null;
    }
}
