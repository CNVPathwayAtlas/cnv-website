/**
 * Phenotype Browser
 * Data model:
 *   D.locations  – genomic regions
 *   D.disorders  – clinical diseases keyed by ORPHA:xxx if possible
 *   D.phenotypes – HPO phenotypes; disorder_entries[] links to disorder_id
 *   D.genes      – gene symbols; location_ids[] links to locations
 *   D.categories – HPO category tree
 *   D.pathways    – WikiPathways pathways; location_ids[] links to locations
 * Filter fields: phenotype | gene | location | disorder | pathway | chromosome | size
 * Grid columns  = filtered disorders
 */
var PhenotypeBrowser = (function () {
    "use strict";

    /* ───── state ───── */
    var D = null, B = "";
    var tipEl, tipCache = {};
    var filters = [];
    var filterOps = [];
    var gridMode = "phenotype";
    var disorderColor = {};
    var locationColor = {};

    /* ───── constants ───── */
    var OPS = {
        gene: [{ v: "equals", l: "=" }, { v: "excludes", l: "≠" }],
        phenotype: [{ v: "equals", l: "=" }, { v: "excludes", l: "≠" }],
        location: [{ v: "equals", l: "=" }, { v: "contains", l: "~" }],
        disorder: [{ v: "equals", l: "=" }, { v: "contains", l: "~" }],
        pathway: [{ v: "equals", l: "=" }],
        chromosome: [{ v: "equals", l: "=" }],
        size: [{ v: "greater", l: ">" }, { v: "less", l: "<" }]
    };
    var FR = { obligate: 4, very_frequent: 3, frequent: 2, occasional: 1 };
    var FR_LABEL = { obligate: "Obligate", very_frequent: "V.Freq", frequent: "Freq", occasional: "Occ" };
    var PAL = [
        "#3b82f6", "#ef4444", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899",
        "#06b6d4", "#84cc16", "#f97316", "#6366f1", "#14b8a6", "#e11d48",
        "#a855f7", "#22c55e", "#eab308", "#0ea5e9", "#d946ef", "#64748b"
    ];
    var defaultLogic = "AND";

    /* Chip display order and labels  */
    var CHIP_FIELD_ORDER = ["phenotype", "gene", "disorder", "location", "pathway", "chromosome", "size"];
    var CHIP_FIELD_LABELS = {
        phenotype: "Phenotypes", gene: "Genes", disorder: "Disorders",
        location: "Locations", pathway: "Pathways", chromosome: "Chromosomes", size: "Size"
    };

    /* ═══════════════════ init / load ═══════════════════ */
    function init() {
        var m = document.querySelector("meta[name=baseurl]");
        B = m ? m.content : "";
        tipEl = document.createElement("div");
        tipEl.className = "hpo-tooltip";
        document.body.appendChild(tipEl);
        load();
    }

    function load() {
        var box = document.getElementById("pheno-loading");
        if (box) box.style.display = "";
        fetch(B + "/assets/data/phenotype_browser_data.json")
            .then(function (r) { return r.json(); })
            .then(function (d) {
                D = d;
                if (box) box.style.display = "none";
                boot();
            })
            .catch(function (e) {
                console.error("Load error", e);
                if (box) box.innerHTML = '<p class="load-error">Failed to load data.</p>';
            });
    }

    function boot() {
        /* assign stable colours */
        var dids = Object.keys(D.disorders).sort();
        dids.forEach(function (did, i) { disorderColor[did] = PAL[i % PAL.length]; });
        D.locations.forEach(function (loc, i) { locationColor[loc.id] = PAL[i % PAL.length]; });

        renderStats();
        buildTree();
        buildGeneList();
        buildLocationList();
        buildDisorderList();
        buildPathwayList();
        buildChrList();
        bindSidebarTabs();
        bindSidebarSearch();
        bindTabs();
        bindGridMode();
        bindFilters();
        refresh();
    }

    function refresh() {
        syncSidebarChecks();
        renderChips();
        renderGrid();
        renderSummary();
    }

    /* ══════════════ stats ══════════════ */
    function renderStats() {
        txt("stat-locations", D.stats.total_locations);
        txt("stat-disorders", D.stats.total_disorders);
        txt("stat-phenotypes", D.stats.total_phenotypes);
        txt("stat-genes", D.stats.total_genes);
    }
    function txt(id, v) { var e = document.getElementById(id); if (e) e.textContent = v; }

    /* Return the location record for a disorder */
    function locFor(dis) {
        for (var i = 0; i < D.locations.length; i++) {
            if (D.locations[i].id === dis.location_id) return D.locations[i];
        }
        return {};
    }

    /* ══════════════ sidebar sync ══════════════ */
    function syncSidebarChecks() {
        var active = {};
        filters.forEach(function (f, i) {
            if (f.source === "sidebar") {
                var key = f.field + "|" + f.value;
                active[key] = f.logic || (i === 0 ? "AND" : (filterOps[i - 1] || "AND"));
            }
        });

        document.querySelectorAll(".tree-pheno").forEach(function (li) {
            var key = "phenotype|" + li.dataset.hpo;
            var logic = active[key];
            li.classList.toggle("selected", !!logic);
            li.querySelectorAll(".sb-logic-btn").forEach(function (btn) {
                btn.classList.toggle("active", !!logic && btn.dataset.logic === logic);
            });
        });

        [
            ["gene-list", "gene"],
            ["location-list", "location"],
            ["disorder-list", "disorder"],
            ["pathway-list", "pathway"],
            ["chr-list", "chromosome"]
        ].forEach(function (pair) {
            var el = document.getElementById(pair[0]); if (!el) return;
            el.querySelectorAll(".sb-item").forEach(function (it) {
                var key = pair[1] + "|" + it.dataset.id;
                var logic = active[key];
                it.classList.toggle("selected", !!logic);
                it.querySelectorAll(".sb-logic-btn").forEach(function (btn) {
                    btn.classList.toggle("active", !!logic && btn.dataset.logic === logic);
                });
            });
        });
    }

    /* ══════════════ helper: AND/OR button pair ══════════════ */
    function logicBtns() {
        return '<span class="sb-logic-btns">'
            + '<button class="sb-logic-btn sb-and-btn" data-logic="AND" title="Add with AND">AND</button>'
            + '<button class="sb-logic-btn sb-or-btn"  data-logic="OR"  title="Add with OR">OR</button>'
            + '</span>';
    }

    /* ══════════════ helper: wire sb-item list clicks ══════════════ */
    function wireSbList(el, field) {
        el.addEventListener("click", function (e) {
            var btn = e.target.closest(".sb-logic-btn");
            if (btn) {
                var it = btn.closest(".sb-item"); if (!it) return;
                toggleSidebarFilter(field, it.dataset.id, btn.dataset.logic);
                return;
            }
            var it2 = e.target.closest(".sb-item");
            if (it2 && !e.target.closest(".sb-logic-btns")) {
                var existing = filters.findIndex(function (f) {
                    return f.field === field && f.op === "equals" && f.value === it2.dataset.id && f.source === "sidebar";
                });
                if (existing >= 0) rmF(existing);
            }
        });
    }

    /* ══════════════ sidebar: phenotype tree ══════════════ */
    function buildTree() {
        var w = document.getElementById("pheno-tree"); if (!w) return;
        var cats = D.categories;
        var keys = Object.keys(cats).sort(function (a, b) {
            return cats[a].label.localeCompare(cats[b].label);
        });
        var h = '<ul class="tree-root">';
        keys.forEach(function (cid) {
            var c = cats[cid], nP = c.phenotype_ids.length;
            var ds = {};
            c.phenotype_ids.forEach(function (pid) {
                var p = D.phenotypes[pid];
                if (p) p.disorder_entries.forEach(function (e) { ds[e.disorder_id] = 1; });
            });
            var nD = Object.keys(ds).length;
            h += '<li class="tree-cat">';
            h += '<div class="tree-cat-hdr" data-cat="' + cid + '">';
            h += '<span class="tree-arrow">&#9654;</span>';
            h += '<span class="tree-cat-label">' + esc(c.label) + '</span>';
            h += '<span class="tree-cat-badge" title="' + nD + ' disorders / ' + nP + ' phenotypes">' + nD + '/' + nP + '</span>';
            h += '</div>';
            h += '<ul class="tree-items" id="ti-' + cid + '">';
            var ps = c.phenotype_ids.slice().sort(function (a, b) {
                var x = D.phenotypes[a] ? D.phenotypes[a].disorder_entries.length : 0;
                var y = D.phenotypes[b] ? D.phenotypes[b].disorder_entries.length : 0;
                return y - x;
            });
            ps.forEach(function (pid) {
                var p = D.phenotypes[pid]; if (!p) return;
                var n = ucntDisorders(p.disorder_entries);
                h += '<li class="tree-pheno" data-hpo="' + pid + '">';
                h += logicBtns();
                h += '<span class="tree-pheno-name">' + esc(p.label) + '</span>';
                h += '<span class="tree-pheno-n">' + n + '</span>';
                h += '</li>';
            });
            h += '</ul></li>';
        });
        h += '</ul>';
        w.innerHTML = h;

        w.addEventListener("click", function (e) {
            var hdr = e.target.closest(".tree-cat-hdr");
            if (hdr) {
                var ul = document.getElementById("ti-" + hdr.dataset.cat);
                var ar = hdr.querySelector(".tree-arrow");
                if (ul) ul.classList.toggle("open");
                if (ar) ar.classList.toggle("expanded");
                return;
            }
            var btn = e.target.closest(".sb-logic-btn");
            if (btn) {
                var li = btn.closest(".tree-pheno");
                if (li) toggleSidebarFilter("phenotype", li.dataset.hpo, btn.dataset.logic);
                return;
            }
            var li2 = e.target.closest(".tree-pheno");
            if (li2 && !e.target.closest(".sb-logic-btns")) {
                var hpo = li2.dataset.hpo;
                var ex = filters.findIndex(function (f) {
                    return f.field === "phenotype" && f.op === "equals" && f.value === hpo && f.source === "sidebar";
                });
                if (ex >= 0) rmF(ex);
            }
        });
        w.addEventListener("mouseover", function (e) {
            var li = e.target.closest(".tree-pheno"); if (li) showTip(li.dataset.hpo, e);
        });
        w.addEventListener("mouseout", function (e) {
            var li = e.target.closest(".tree-pheno"); if (li) hideTip();
        });
        w.addEventListener("mousemove", function (e) { moveTip(e); });
    }

    /* ══════════════ sidebar: genes ══════════════ */
    function buildGeneList() {
        var w = document.getElementById("gene-list"); if (!w) return;
        var genes = Object.keys(D.genes).sort();
        var h = "";
        genes.forEach(function (sym) {
            var g = D.genes[sym];
            h += '<div class="sb-item" data-type="gene" data-id="' + esc(sym) + '">';
            h += logicBtns();
            h += '<span class="sb-item-label" title="' + esc(g.name) + '">' + esc(sym) + '</span>';
            h += '<span class="sb-item-badge">' + g.location_ids.length + '</span>';
            h += '</div>';
        });
        w.innerHTML = h;
        wireSbList(w, "gene");
    }

    /* ══════════════ sidebar: locations ══════════════ */
    function buildLocationList() {
        var w = document.getElementById("location-list"); if (!w) return;
        var locs = D.locations.slice().sort(function (a, b) { return a.id.localeCompare(b.id); });
        var h = "";
        locs.forEach(function (loc) {
            h += '<div class="sb-item" data-type="location" data-id="' + esc(loc.id) + '">';
            h += logicBtns();
            h += '<span class="sb-color-dot" style="background:' + (locationColor[loc.id] || "#64748b") + '"></span>';
            h += '<span class="sb-item-label">' + esc(loc.id) + '</span>';
            h += '<span class="sb-item-badge">chr' + loc.chromosome + ' · ' + (loc.gene_count || 0) + 'g</span>';
            h += '</div>';
        });
        w.innerHTML = h;
        wireSbList(w, "location");
    }

    /* ══════════════ sidebar: disorders ══════════════ */
    function buildDisorderList() {
        var w = document.getElementById("disorder-list"); if (!w) return;
        var dids = Object.keys(D.disorders).sort();
        var h = "";
        dids.forEach(function (did) {
            var d = D.disorders[did];
            var isLoc = d.no_orphacode;
            h += '<div class="sb-item" data-type="disorder" data-id="' + esc(did) + '">';
            h += logicBtns();
            h += '<span class="sb-color-dot" style="background:' + (disorderColor[did] || "#64748b") + '"></span>';
            h += '<span class="sb-item-label">';
            if (isLoc) {
                h += '<em title="No ORPHA code">' + esc(d.name) + '</em>';
            } else {
                h += '<strong>' + esc(did) + '</strong>';
                if (d.name) h += ' <small>' + esc(d.name) + '</small>';
            }
            h += '</span>';
            h += '<span class="sb-item-badge">' + esc(d.location_id) + (d.cause ? ' · ' + esc(d.cause) : '') + '</span>';
            h += '</div>';
        });
        w.innerHTML = h;
        wireSbList(w, "disorder");
    }

    /* ══════════════ sidebar: WikiPathways ══════════════ */
    function buildPathwayList() {
        var w = document.getElementById("pathway-list"); if (!w) return;
        var pwMap = {};
        D.locations.forEach(function (loc) {
            if (!loc.wikipathways_id) return;
            var wpid = loc.wikipathways_id;
            if (!pwMap[wpid]) pwMap[wpid] = { id: wpid, name: loc.pathway_name || wpid, location_ids: [] };
            pwMap[wpid].location_ids.push(loc.id);
        });
        var wpids = Object.keys(pwMap).sort();
        var h = "";
        wpids.forEach(function (wpid) {
            var pw = pwMap[wpid];
            h += '<div class="sb-item" data-type="pathway" data-id="' + esc(wpid) + '">';
            h += logicBtns();
            h += '<span class="sb-item-label">'
                + '<a class="sb-pathway-link" href="https://www.wikipathways.org/pathways/' + esc(wpid) + '.html"'
                + ' target="_blank" rel="noopener" title="' + esc(wpid) + '">'
                + esc(pw.name) + ' &#8599;</a>'
                + '</span>';
            h += '<span class="sb-item-badge">' + pw.location_ids.length + ' loc</span>';
            h += '</div>';
        });
        w.innerHTML = h || '<p class="pheno-empty" style="font-size:0.7rem">No pathways in data</p>';
        wireSbList(w, "pathway");
    }

    /* ══════════════ sidebar: chromosomes ══════════════ */
    function buildChrList() {
        var w = document.getElementById("chr-list"); if (!w) return;
        var chrMap = {};
        D.locations.forEach(function (loc) {
            var ch = String(loc.chromosome);
            if (!chrMap[ch]) chrMap[ch] = 0;
            chrMap[ch]++;
        });
        var chrs = Object.keys(chrMap).sort(function (a, b) {
            var na = parseInt(a, 10), nb = parseInt(b, 10);
            if (!isNaN(na) && !isNaN(nb)) return na - nb;
            return a.localeCompare(b);
        });
        var h = "";
        chrs.forEach(function (ch) {
            h += '<div class="sb-item" data-type="chromosome" data-id="' + ch + '">';
            h += logicBtns();
            h += '<span class="sb-item-label">chr' + esc(ch) + '</span>';
            h += '<span class="sb-item-badge">' + chrMap[ch] + ' loc</span>';
            h += '</div>';
        });
        w.innerHTML = h;
        wireSbList(w, "chromosome");
    }

    /* ══════════════ shared tab-switching helper ══════════════ */
    function bindTabGroup(tabSel, panelSel, activeClass, idFn) {
        document.querySelectorAll(tabSel).forEach(function (tab) {
            tab.addEventListener("click", function () {
                document.querySelectorAll(tabSel).forEach(function (t) { t.classList.remove("active"); });
                tab.classList.add("active");
                document.querySelectorAll(panelSel).forEach(function (p) { p.classList.remove("active"); });
                var tgt = document.getElementById(idFn(tab));
                if (tgt) tgt.classList.add("active");
            });
        });
    }

    /* ══════════════ sidebar tabs ══════════════ */
    function bindSidebarTabs() {
        bindTabGroup(".sidebar-tab", ".sidebar-panel", "active", function (tab) { return "sb-" + tab.dataset.sidebar; });
        /* clear search when switching tabs */
        document.querySelectorAll(".sidebar-tab").forEach(function (tab) {
            tab.addEventListener("click", function () {
                var si = document.getElementById("sidebar-search-input");
                if (si) { si.value = ""; filterSidebarItems(""); }
            });
        });
    }

    function bindSidebarSearch() {
        var inp = document.getElementById("sidebar-search-input"); if (!inp) return;
        inp.addEventListener("input", function () { filterSidebarItems(inp.value.trim().toLowerCase()); });
    }

    function filterSidebarItems(q) {
        document.querySelectorAll("#pheno-tree .tree-cat").forEach(function (cat) {
            var catLabel = (cat.querySelector(".tree-cat-label") || {}).textContent || "";
            var catMatch = !q || catLabel.toLowerCase().indexOf(q) >= 0;
            var anyPheno = false;
            cat.querySelectorAll(".tree-pheno").forEach(function (ph) {
                var name = (ph.querySelector(".tree-pheno-name") || {}).textContent || "";
                var match = !q || name.toLowerCase().indexOf(q) >= 0 || catMatch;
                ph.style.display = match ? "" : "none";
                if (match) anyPheno = true;
            });
            cat.style.display = (catMatch || anyPheno) ? "" : "none";
        });
        ["gene-list", "location-list", "disorder-list", "pathway-list", "chr-list"].forEach(function (id) {
            var el = document.getElementById(id); if (!el) return;
            el.querySelectorAll(".sb-item").forEach(function (it) {
                var label = (it.querySelector(".sb-item-label") || {}).textContent || "";
                it.style.display = (!q || label.toLowerCase().indexOf(q) >= 0) ? "" : "none";
            });
        });
    }

    /* ══════════════ main tabs ══════════════ */
    function bindTabs() {
        bindTabGroup(".pheno-tab", ".pheno-tab-content", "active", function (tab) { return tab.dataset.target; });
    }

    /* ══════════════ grid mode ══════════════ */
    function bindGridMode() {
        var sel = document.getElementById("olap-mode");
        if (sel) sel.addEventListener("change", function () { gridMode = sel.value; renderGrid(); });
    }

    /* ══════════════ render grid ══════════════ */
    function renderGrid() {
        var w = document.getElementById("olap-grid-container"); if (!w) return;

        if (!filters.length) {
            w.innerHTML = '<p class="pheno-empty">Select phenotypes, genes, disorders or locations from the sidebar, '
                + 'or use the filter builder above to get started.</p>';
            return;
        }

        var disorders = filteredDisorders();
        if (!disorders.length) {
            w.innerHTML = '<p class="pheno-empty">No disorders match current filters.</p>';
            return;
        }

        var cats = D.categories;
        var sk = Object.keys(cats).sort(function (a, b) { return cats[a].label.localeCompare(cats[b].label); });
        var activePhenoValues = [];
        filters.forEach(function (f) {
            if (f.field === "phenotype" && f.op === "equals") activePhenoValues.push(f.value);
        });

        var rowDefs;
        if (gridMode === "phenotype" && activePhenoValues.length > 0) {
            var pids = [];
            activePhenoValues.forEach(function (val) {
                Object.keys(D.phenotypes).forEach(function (pid) {
                    var p = D.phenotypes[pid];
                    if ((pid === val || p.label === val) && pids.indexOf(pid) < 0) pids.push(pid);
                });
            });
            if (pids.length > 0) {
                rowDefs = pids.slice(0, 60).map(function (pid) {
                    var p = D.phenotypes[pid];
                    return { id: pid, label: p ? p.label : pid, pids: [pid] };
                });
            } else {
                rowDefs = sk.map(function (cid) {
                    return { id: cid, label: shortCat(cats[cid].label), pids: cats[cid].phenotype_ids };
                });
            }
        } else {
            rowDefs = sk.map(function (cid) {
                return { id: cid, label: shortCat(cats[cid].label), pids: cats[cid].phenotype_ids };
            });
        }

        var h = '<div class="grid-scroll"><table class="olap-grid"><thead><tr>';
        h += '<th class="sticky-col">Phenotype</th>';
        disorders.forEach(function (dis) {
            var loc = locFor(dis);
            var col = disorderColor[dis.id] || "#64748b";
            h += '<th class="th-horiz" title="' + esc(dis.id) + ' – ' + esc(dis.cause) + ' at ' + esc(dis.location_id) + '" '
                + 'style="border-top:3px solid ' + col + '">'
                + '<a class="cnv-link" href="' + B + (loc.url || '') + '">'
                + esc(dis.id) + '</a>'
                + '<br><span style="font-size:0.55rem;font-weight:400;color:#64748b">'
                + esc(dis.location_id) + ' ' + esc(dis.cause) + '</span>'
                + '</th>';
        });
        h += '</tr></thead><tbody>';

        rowDefs.forEach(function (row) {
            h += '<tr>';
            h += '<td class="sticky-col" title="' + esc(row.label) + '">' + esc(row.label) + '</td>';
            disorders.forEach(function (dis) {
                var f = bfreqRowDisorder(dis, row.pids);
                if (f) {
                    var label = FR_LABEL[f.f] || f.f;
                    h += '<td class="freq-cell freq-text freq-text-' + f.f + '" title="' + esc(f.l) + ' (' + f.f.replace(/_/g, " ") + ')">'
                        + label + '</td>';
                } else {
                    h += '<td class="freq-cell empty-cell">&middot;</td>';
                }
            });
            h += '</tr>';
        });
        h += '</tbody></table></div>';
        w.innerHTML = h;
    }

    function bfreqRowDisorder(disorder, pids) {
        var best = null, bl = "";
        pids.forEach(function (pid) {
            var p = D.phenotypes[pid]; if (!p) return;
            p.disorder_entries.forEach(function (e) {
                if (e.disorder_id === disorder.id) {
                    var s = FR[e.frequency] || 0;
                    if (!best || s > (FR[best] || 0)) { best = e.frequency; bl = p.label; }
                }
            });
        });
        return best ? { f: best, l: bl } : null;
    }

    /* ══════════════ filtering ══════════════ */
    function filteredDisorders() {
        var allDisorders = Object.values(D.disorders);
        if (!filters.length) return allDisorders;
        return allDisorders.filter(function (dis) {
            var result = evalFDisorder(dis, filters[0]);
            for (var i = 1; i < filters.length; i++) {
                var op = filterOps[i - 1] || "AND";
                var r = evalFDisorder(dis, filters[i]);
                if (op === "AND") result = result && r;
                else result = result || r;
            }
            return result;
        });
    }

    function evalFDisorder(dis, f) {
        var v = f.value.toLowerCase();
        var loc = locFor(dis);

        if (f.field === "disorder") {
            // match ORPHA id, LOC: id, or human-readable name
            var idMatch = dis.id.toLowerCase().indexOf(v) >= 0;
            var nameMatch = (dis.name || "").toLowerCase().indexOf(v) >= 0;
            // also match bare orphacode number
            var codeMatch = dis.orphacode && String(dis.orphacode).indexOf(v) >= 0;
            if (f.op === "contains") return idMatch || nameMatch;
            return idMatch || nameMatch || codeMatch;
        }
        if (f.field === "location") {
            // selecting a location returns ALL its disorders
            var locMatch = f.op === "contains"
                ? (loc.id || "").toLowerCase().indexOf(v) >= 0
                : (loc.id || "").toLowerCase() === v;
            return locMatch;
        }
        if (f.field === "chromosome") {
            return String(loc.chromosome || "").toLowerCase() === v;
        }
        if (f.field === "size") {
            var sz = (loc.end || 0) - (loc.start || 0), th = parseFloat(v);
            if (isNaN(th)) return true;
            return f.op === "greater" ? sz > th : sz < th;
        }
        if (f.field === "gene") {
            var gl = (loc.gene_symbols || []).map(function (g) { return g.toLowerCase(); });
            return f.op === "excludes" ? gl.indexOf(v) < 0 : gl.indexOf(v) >= 0;
        }
        if (f.field === "pathway") {
            var wpid = (loc.wikipathways_id || "").toLowerCase();
            var wpname = (loc.pathway_name || "").toLowerCase();
            return wpid === v || wpid.indexOf(v) >= 0 || wpname.indexOf(v) >= 0;
        }
        if (f.field === "phenotype") {
            var found = false;
            Object.keys(D.phenotypes).forEach(function (pid) {
                var p = D.phenotypes[pid];
                if (pid.toLowerCase() === v || p.label.toLowerCase() === v) {
                    p.disorder_entries.forEach(function (e) {
                        if (e.disorder_id === dis.id) found = true;
                    });
                }
            });
            return f.op === "excludes" ? !found : found;
        }
        return true;
    }

    /* ══════════════ toggle sidebar filter ══════════════ */
    function toggleSidebarFilter(field, value, logic) {
        var idx = -1;
        for (var i = 0; i < filters.length; i++) {
            if (filters[i].field === field && filters[i].op === "equals"
                && filters[i].value === value && filters[i].source === "sidebar") {
                idx = i; break;
            }
        }
        if (idx >= 0) {
            if (filters[idx].logic === logic) {
                rmF(idx);
            } else {
                filters[idx].logic = logic;
                if (idx > 0) filterOps[idx - 1] = logic;
                refresh();
            }
        } else {
            addF({ field: field, op: "equals", value: value, source: "sidebar", logic: logic || "AND" }, logic || "AND");
        }
    }

    /* ══════════════ filter builder ══════════════ */
    function bindFilters() {
        var fld = document.getElementById("filter-field");
        var ops = document.getElementById("filter-op");
        var val = document.getElementById("filter-value");
        var addB = document.getElementById("filter-add-btn");
        var clrB = document.getElementById("filter-clear-btn");
        if (!fld) return;
        syncOps(fld, ops, val);
        fld.addEventListener("change", function () { syncOps(fld, ops, val); });

        if (val) {
            var acWrap = document.createElement("div");
            acWrap.className = "filter-ac-wrap";
            val.parentNode.insertBefore(acWrap, val);
            acWrap.appendChild(val);
            var acBox = document.createElement("div");
            acBox.className = "filter-ac-box";
            acWrap.appendChild(acBox);

            val.addEventListener("input", function () {
                var q = val.value.trim(), fi = fld.value;
                if (q.length < 1 || fi === "size") { acBox.innerHTML = ""; acBox.classList.remove("open"); return; }
                var sg = suggest(fi, q);
                if (!sg.length) { acBox.innerHTML = ""; acBox.classList.remove("open"); return; }
                acBox.innerHTML = sg.map(function (s) { return '<div class="fac-item">' + esc(s) + '</div>'; }).join("");
                acBox.classList.add("open");
            });
            val.addEventListener("blur", function () {
                setTimeout(function () { acBox.innerHTML = ""; acBox.classList.remove("open"); }, 200);
            });
            acBox.addEventListener("mousedown", function (e) {
                var it = e.target.closest(".fac-item");
                if (it) {
                    e.preventDefault(); e.stopPropagation();
                    // suggestions for disorder/pathway include " – Name" suffix — strip it
                    var text = it.textContent;
                    var dashIdx = text.indexOf(" \u2013 ");
                    var fi = fld.value;
                    if (dashIdx >= 0 && (fi === "disorder" || fi === "pathway")) {
                        text = text.substring(0, dashIdx);
                    }
                    val.value = text;
                    acBox.innerHTML = ""; acBox.classList.remove("open");
                }
            });
            val.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    var v = val.value.trim(); if (!v) return;
                    addF({ field: fld.value, op: ops.value, value: v });
                    val.value = ""; acBox.innerHTML = ""; acBox.classList.remove("open");
                }
            });
        }

        if (addB) addB.addEventListener("click", function () {
            var v = val ? val.value.trim() : ""; if (!v) return;
            addF({ field: fld.value, op: ops.value, value: v });
            if (val) val.value = "";
        });
        if (clrB) clrB.addEventListener("click", function () { filters = []; filterOps = []; refresh(); });
    }

    function syncOps(fld, ops, val) {
        fld = fld || document.getElementById("filter-field");
        ops = ops || document.getElementById("filter-op");
        val = val || document.getElementById("filter-value");
        if (!fld || !ops) return;
        var f = fld.value, list = OPS[f] || [];
        ops.innerHTML = "";
        list.forEach(function (o) {
            var opt = document.createElement("option");
            opt.value = o.v; opt.textContent = o.l; ops.appendChild(opt);
        });
        if (val) {
            var ph = {
                gene: "e.g. TUBGCP5",
                phenotype: "e.g. Intellectual disability",
                location: "e.g. 22q11.21",
                disorder: "e.g. ORPHA:567",
                pathway: "e.g. WP4657",
                chromosome: "e.g. 22",
                size: "e.g. 1000000"
            };
            val.placeholder = ph[f] || "Value…";
            val.type = f === "size" ? "number" : "text";
        }
    }

    function suggest(field, q) {
        q = q.toLowerCase(); var r = [];
        if (field === "gene") {
            Object.keys(D.genes).forEach(function (s) { if (s.toLowerCase().indexOf(q) >= 0) r.push(s); });
        } else if (field === "location") {
            D.locations.forEach(function (l) { if (l.id.toLowerCase().indexOf(q) >= 0) r.push(l.id); });
        } else if (field === "disorder") {
            Object.keys(D.disorders).forEach(function (did) {
                var dis = D.disorders[did];
                var idMatch = did.toLowerCase().indexOf(q) >= 0;
                var nameMatch = (dis.name || "").toLowerCase().indexOf(q) >= 0;
                if (idMatch || nameMatch) {
                    // show "ORPHA:567 – name" or just the id for LOC: entries
                    var label = dis.name ? did + " \u2013 " + dis.name : did;
                    r.push(label);
                }
            });
        } else if (field === "pathway") {
            // build unique pathway map with names
            var seen = {};
            D.locations.forEach(function (l) {
                var wpid = l.wikipathways_id;
                if (!wpid || seen[wpid]) return;
                seen[wpid] = true;
                var name = l.pathway_name || "";
                var idMatch = wpid.toLowerCase().indexOf(q) >= 0;
                var nameMatch = name.toLowerCase().indexOf(q) >= 0;
                if (idMatch || nameMatch) {
                    r.push(name ? wpid + " \u2013 " + name : wpid);
                }
            });
        } else if (field === "phenotype") {
            Object.keys(D.phenotypes).forEach(function (pid) {
                var p = D.phenotypes[pid];
                if (p.label.toLowerCase().indexOf(q) >= 0 || pid.toLowerCase().indexOf(q) >= 0) r.push(p.label);
            });
        } else if (field === "chromosome") {
            var seen2 = {};
            D.locations.forEach(function (l) {
                var ch = String(l.chromosome);
                if (ch.indexOf(q) >= 0 && !seen2[ch]) { seen2[ch] = true; r.push(ch); }
            });
        }
        return r.slice(0, 15);
    }

    function addF(f, logic) {
        if (!f.source) f.source = "builder";
        if (f.source === "sidebar") {
            var dup = filters.some(function (x) {
                return x.field === f.field && x.op === f.op && x.value === f.value;
            });
            if (dup) return;
        }
        if (filters.length > 0) filterOps.push(logic || defaultLogic);
        filters.push(f);
        refresh();
    }

    function rmF(i) {
        filters.splice(i, 1);
        if (filterOps.length >= i && i > 0) filterOps.splice(i - 1, 1);
        else if (filterOps.length > 0) filterOps.splice(0, 1);
        refresh();
    }

    /* ══════════════ chips ══════════════ */
    function renderChips() {
        var el = document.getElementById("active-filters"); if (!el) return;
        if (!filters.length) { el.innerHTML = '<span class="no-filters">No active filters</span>'; return; }

        var groups = {};
        filters.forEach(function (f, i) {
            if (!groups[f.field]) groups[f.field] = [];
            groups[f.field].push({ filter: f, index: i });
        });

        var h = "";
        CHIP_FIELD_ORDER.forEach(function (field) {
            var items = groups[field]; if (!items || !items.length) return;
            h += '<div class="chip-group">';
            h += '<span class="chip-group-label">' + CHIP_FIELD_LABELS[field] + ':</span>';
            items.forEach(function (item, gi) {
                var f = item.filter, idx = item.index;
                if (gi > 0) {
                    var opIdx = idx - 1;
                    var logic = (opIdx >= 0 && filterOps[opIdx]) ? filterOps[opIdx] : "AND";
                    h += '<span class="chip chip-logic chip-logic-toggle" data-oidx="' + opIdx + '">' + logic + '</span>';
                }
                var chipLabel = "";
                if (f.field === "phenotype") {
                    var p = D.phenotypes[f.value]; chipLabel = p ? p.label : f.value;
                } else if (f.field === "disorder") {
                    var d = D.disorders[f.value];
                    if (d) {
                        if (d.no_orphacode) {
                            chipLabel = d.name || f.value;
                        } else {
                            chipLabel = f.value + (d.name ? " \u2013 " + d.name : "");
                        }
                    } else {
                        chipLabel = f.value;
                    }
                } else if (f.field === "chromosome") {
                    chipLabel = "chr" + f.value;
                } else if (f.field === "size") {
                    chipLabel = (f.op === "greater" ? "> " : "< ") + f.value;
                } else if (f.op === "excludes") {
                    chipLabel = "NOT " + f.value;
                } else if (f.op === "contains") {
                    chipLabel = "~" + f.value;
                } else {
                    chipLabel = f.value;
                }
                var chipClass = "chip chip-" + field;
                h += '<span class="' + chipClass + '">' + esc(chipLabel)
                    + ' <span class="chip-x" data-i="' + idx + '">\u00d7</span></span>';
            });
            h += '</div>';
        });

        el.innerHTML = h;
        el.querySelectorAll(".chip-x").forEach(function (btn) {
            btn.addEventListener("click", function () { rmF(parseInt(btn.dataset.i, 10)); });
        });
        el.querySelectorAll(".chip-logic-toggle").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var oi = parseInt(btn.dataset.oidx, 10);
                if (oi >= 0 && oi < filterOps.length) {
                    filterOps[oi] = filterOps[oi] === "AND" ? "OR" : "AND";
                    refresh();
                }
            });
        });
    }

    /* ══════════════ summary tab ══════════════ */
    function renderSummary() {
        var tb = document.getElementById("pub-summary-body"); if (!tb) return;
        if (!filters.length) {
            tb.innerHTML = '<tr><td colspan="6" class="pheno-empty">Add filters to see summary data.</td></tr>';
            txt("summary-count", "0 disorders");
            return;
        }
        var rows = filteredDisorders(), h = "";
        rows.forEach(function (dis) {
            var loc = locFor(dis);
            var pl = disorderPhenos(dis);
            h += '<tr>';
            h += '<td>' + esc(dis.id) + '</td>';
            h += '<td><a class="cnv-link" href="' + B + (loc.url || "") + '">' + esc(dis.location_id) + '</a>'
                + ' <small>' + esc(dis.cause) + '</small></td>';
            h += '<td>chr' + (loc.chromosome || "") + ':' + (loc.start || 0).toLocaleString()
                + '–' + (loc.end || 0).toLocaleString() + '</td>';
            h += '<td>' + ((loc.end || 0) - (loc.start || 0) > 0
                ? (((loc.end - loc.start) / 1e3).toFixed(1) + ' kb') : '–') + '</td>';
            h += '<td class="gene-list">' + esc((loc.gene_symbols || []).join(", ")) + '</td>';
            h += '<td class="pheno-summary-cell">' + pl.map(function (p) {
                return '<span title="' + esc(p.id) + '">' + esc(p.label) + '</span>';
            }).join(", ") + '</td>';
            h += '</tr>';
        });
        tb.innerHTML = h;
        txt("summary-count", rows.length + " disorder" + (rows.length !== 1 ? "s" : ""));
    }

    function disorderPhenos(dis) {
        var out = [], seen = {};
        Object.keys(D.phenotypes).forEach(function (pid) {
            D.phenotypes[pid].disorder_entries.forEach(function (e) {
                if (e.disorder_id === dis.id && !seen[pid]) {
                    seen[pid] = 1;
                    out.push({ id: pid, label: D.phenotypes[pid].label, frequency: e.frequency });
                }
            });
        });
        return out;
    }

    /* ══════════════ OLS tooltip ══════════════ */
    function showTip(hpo, evt) {
        if (!tipEl) return;
        if (tipCache[hpo]) renderTip(hpo, tipCache[hpo]);
        else {
            var p = D.phenotypes[hpo];
            tipEl.innerHTML = '<div class="tip-title">' + esc(p ? p.label : hpo) + '</div>'
                + '<div class="tip-id">' + hpo + '</div><div class="tip-loading">Loading from OLS…</div>';
            tipEl.style.display = "block";
            fetchOLS(hpo);
        }
        moveTip(evt);
        tipEl.style.display = "block";
    }
    function hideTip() { if (tipEl) tipEl.style.display = "none"; }
    function moveTip(evt) {
        if (!tipEl || tipEl.style.display === "none") return;
        var x = evt.clientX + 14, y = evt.clientY + 14;
        var r = tipEl.getBoundingClientRect();
        if (x + r.width > window.innerWidth) x = evt.clientX - r.width - 10;
        if (y + r.height > window.innerHeight) y = evt.clientY - r.height - 10;
        tipEl.style.left = x + "px"; tipEl.style.top = y + "px";
    }
    function fetchOLS(hpo) {
        var iri = encodeURIComponent(encodeURIComponent("http://purl.obolibrary.org/obo/" + hpo.replace(":", "_")));
        fetch("https://www.ebi.ac.uk/ols4/api/v2/ontologies/hp/classes/" + iri + "?lang=en")
            .then(function (r) { return r.json(); })
            .then(function (d) {
                var def = "";
                if (d.definition && d.definition.length)
                    def = typeof d.definition[0] === "string" ? d.definition[0] : (d.definition[0].value || "");
                var sy = [];
                if (d.synonym) d.synonym.forEach(function (s) { sy.push(typeof s === "string" ? s : (s.value || "")); });
                tipCache[hpo] = { label: d.label ? (Array.isArray(d.label) ? d.label[0] : d.label) : "", definition: def, synonyms: sy.slice(0, 4) };
                renderTip(hpo, tipCache[hpo]);
            })
            .catch(function () { tipCache[hpo] = { label: "", definition: "", synonyms: [] }; });
    }
    function renderTip(hpo, info) {
        if (!tipEl) return;
        var p = D.phenotypes[hpo], label = info.label || (p ? p.label : hpo);
        var h = '<div class="tip-title">' + esc(label) + '</div><div class="tip-id">' + hpo + '</div>';
        if (info.definition) {
            var def = info.definition.length > 250 ? info.definition.substring(0, 248) + "…" : info.definition;
            h += '<div class="tip-def">' + esc(def) + '</div>';
        }
        if (info.synonyms && info.synonyms.length)
            h += '<div class="tip-syns"><strong>Synonyms:</strong> ' + info.synonyms.map(esc).join(", ") + '</div>';
        tipEl.innerHTML = h;
    }

    /* ══════════════ export ══════════════ */
    function exportCSV() {
        var rows = filteredDisorders();
        var csv = [["Disorder (ORPHA)", "Location", "Cause", "Coordinates", "Size (bp)", "Gene Count", "Genes", "HPO Terms"]];
        rows.forEach(function (dis) {
            var loc = locFor(dis);
            var pl = disorderPhenos(dis);
            csv.push([
                dis.id, dis.location_id, dis.cause,
                "chr" + (loc.chromosome || "") + ":" + (loc.start || 0) + "-" + (loc.end || 0),
                (loc.end || 0) - (loc.start || 0), loc.gene_count || 0,
                (loc.gene_symbols || []).join("; "),
                pl.map(function (p) { return p.label + " (" + p.id + ")"; }).join("; ")
            ]);
        });
        var t = csv.map(function (r) {
            return r.map(function (c) { return '"' + String(c).replace(/"/g, '""') + '"'; }).join(",");
        }).join("\n");
        var blob = new Blob([t], { type: "text/csv" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a"); a.href = url; a.download = "phenotype_browser_export.csv"; a.click();
        URL.revokeObjectURL(url);
    }

    /* ══════════════ helpers ══════════════ */
    function esc(s) {
        if (!s) return "";
        return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
    function ucntDisorders(entries) {
        var ids = {}; entries.forEach(function (e) { ids[e.disorder_id] = 1; }); return Object.keys(ids).length;
    }
    function shortCat(l) {
        return l.replace(/^Abnormality of the /, "").replace(/^Abnormality of /, "").replace(/^Phenotypic abnormality$/, "Other");
    }

    return { init: init, exportCSV: exportCSV };
})();

document.addEventListener("DOMContentLoaded", function () { PhenotypeBrowser.init(); });
