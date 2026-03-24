$(document).ready(function () {
    if ($('#gene-info-table').length) {
        $('#gene-info-table').DataTable();
    }

    var controls = document.querySelector('.jbrowse-controls');
    var frame = document.getElementById('jbrowse-frame');
    var coordsLabel = document.querySelector('.jbrowse-coords');
    if (controls && frame && coordsLabel) {
        var urls = {
            hg19: controls.dataset.hg19Url,
            hg38: controls.dataset.hg38Url,
        };

        var coords = {
            hg19: coordsLabel.dataset.hg19Loc,
            hg38: coordsLabel.dataset.hg38Loc,
        };

        var defaultAssembly = controls.dataset.defaultAssembly;
        if (!urls[defaultAssembly]) {
            defaultAssembly = urls.hg19 ? 'hg19' : 'hg38';
        }

        function setAssembly(assembly) {
            if (!urls[assembly]) return;
            frame.src = urls[assembly];
            coordsLabel.textContent = coords[assembly] || '';
            document.querySelectorAll('.jbrowse-switch').forEach(function (button) {
                var isActive = button.dataset.targetAssembly === assembly;
                button.classList.toggle('is-active', isActive);
                button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            });
        }

        document.querySelectorAll('.jbrowse-switch').forEach(function (button) {
            button.addEventListener('click', function () {
                setAssembly(button.dataset.targetAssembly);
            });
        });

        setAssembly(defaultAssembly);
    }

    // Phenotype grouping
    if (typeof PhenotypeGrouper !== 'undefined') {
        initPhenotypeGrouping();
    }

    // Expand all details before printing, restore after
    var originalPageLength;
    window.addEventListener('beforeprint', function () {
        // Expand all phenotype details
        document.querySelectorAll('details').forEach(function (detail) {
            detail.dataset.wasOpen = detail.open;
            detail.open = true;
        });

        // Show all rows in DataTable
        if ($.fn.DataTable && $('#gene-info-table').length) {
            var table = $('#gene-info-table').DataTable();
            originalPageLength = table.page.len();
            table.page.len(-1).draw();
        }
    });

    window.addEventListener('afterprint', function () {
        // Restore phenotype details state
        document.querySelectorAll('details').forEach(function (detail) {
            detail.open = detail.dataset.wasOpen === 'true';
        });

        // Restore DataTable pagination
        if ($.fn.DataTable && $('#gene-info-table').length && originalPageLength) {
            var table = $('#gene-info-table').DataTable();
            table.page.len(originalPageLength).draw();
        }
    });
});

async function initPhenotypeGrouping() {
    var jsonScripts = document.querySelectorAll('script[data-phenotypes-json]');

    for (var script of jsonScripts) {
        var orphaIndex = script.dataset.orphaIndex;
        var table = document.querySelector('table[data-phenotype-table][data-orpha-index="' + orphaIndex + '"]');
        if (!table) continue;

        try {
            var data = JSON.parse(script.textContent);
            var freqColumns = ['obligate', 'very_frequent', 'frequent', 'occasional'];

            for (var freq of freqColumns) {
                var phenotypes = data[freq];
                if (!phenotypes || phenotypes.length === 0) continue;

                var cell = table.querySelector('td[data-freq="' + freq + '"]');
                if (!cell) continue;

                var groups = await PhenotypeGrouper.groupPhenotypes(phenotypes);
                cell.innerHTML = renderGroupedPhenotypes(groups);
            }
        } catch (e) {
            console.error('Error grouping phenotypes:', e);
        }
    }
}

function renderGroupedPhenotypes(groups) {
    if (!groups || groups.length === 0) {
        return '<span class="no-phenotypes">No phenotypes available for now</span>';
    }

    return groups.map(function (group) {
        var items = group.phenotypes.map(function (p) {
            var link = 'https://hpo.jax.org/app/browse/term/' + p.hpo_id;
            return '<li><a href="' + link + '" target="_blank">' + p.name + '</a></li>';
        }).join('');

        var parentLabel = group.parent.label;
        var parentLink = group.parent.id
            ? '<a href="https://hpo.jax.org/app/browse/term/' + group.parent.id + '" target="_blank">' + parentLabel + '</a>'
            : parentLabel;

        return '<div class="phenotype-group">' +
            '<details>' +
            '<summary class="group-header">' + parentLink + ' <span class="group-count">(' + group.phenotypes.length + ')</span></summary>' +
            '<ul class="phenotype-list grouped">' + items + '</ul>' +
            '</details>' +
            '</div>';
    }).join('');
}