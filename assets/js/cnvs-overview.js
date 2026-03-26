document.addEventListener("DOMContentLoaded", function () {
    const table = $('#cnvs-table').DataTable({
        order: [[2, 'asc'], [3, 'asc']],
        language: {
            lengthMenu: 'Show _MENU_'
        }
    });

    // Toggle show more/less genes
    document.getElementById('cnvs-table').addEventListener('click', function (e) {
        const target = e.target;
        if (target.classList.contains('show-more') || target.classList.contains('show-less')) {
            e.preventDefault();
            const index = target.dataset.index;
            const genes = JSON.parse(target.dataset.genes);
            const container = document.getElementById("gene-container-" + index);

            if (target.classList.contains("show-more")) {
                container.innerText = genes.join(", ");
                target.innerText = "less";
                target.classList.remove("show-more");
                target.classList.add("show-less");
            } else {
                container.innerText = genes.slice(0, 3).join(", ");
                target.innerText = "more";
                target.classList.remove("show-less");
                target.classList.add("show-more");
            }
        }
    });

    // Custom filter: default search + gene search
    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
        const input = $('#cnvs-table_filter input').val().toLowerCase().trim();

        // If input is empty, show all rows
        if (!input) return true;

        const searchTerms = input.split(/[\s,]+/).filter(term => term !== '');
        const rowText = data.join(' ').toLowerCase();

        // Default DataTables behavior: match anywhere
        if (rowText.includes(input)) return true;

        // Fallback: check Genes column (index 8)
        const geneColumn = data[8].toLowerCase();
        return searchTerms.some(term => geneColumn.includes(term));
    });

    // Trigger search filter redraw
    $('#cnvs-table_filter input').off().on('keyup change', function () {
        table.draw();
    });
});