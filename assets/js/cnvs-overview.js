// GRCh37 chromosome lengths (bp), GRCh37.p13 primary assembly
var CHROMOSOME_LENGTHS = {
  "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276, "5": 180915260,
  "6": 171115067, "7": 159138663, "8": 146364022, "9": 141213431, "10": 135534747,
  "11": 135006516, "12": 133851895, "13": 115169878, "14": 107349540, "15": 102531392,
  "16": 90354753, "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
  "21": 48129895, "22": 51304566, "X": 155270560, "Y": 59373566
};

document.addEventListener("DOMContentLoaded", function () {
  var tableElement = document.getElementById("cnvs-table");
  var geneColumn = $(tableElement).find("th.genes-column").index();
  // Get all rows before DataTables removes the rows of the other pages
  var rows = Array.from(tableElement.querySelectorAll("tbody tr"));
  var table = $(tableElement).DataTable({
    order: [[2, "asc"], [3, "asc"]],
    language: { lengthMenu: "Show _MENU_" }
  });

  var filters = {
    chromosome: document.getElementById("filter-chromosome"),
    type: document.getElementById("filter-type"),
    orpha: document.getElementById("filter-orpha")
  };

  // Fill the chromosome filter with the chromosomes in the table
  var chromosomes = [];
  rows.forEach(function (row) {
    if (chromosomes.indexOf(row.dataset.chromosome) === -1) chromosomes.push(row.dataset.chromosome);
  });
  Object.keys(CHROMOSOME_LENGTHS).filter(function (c) { return chromosomes.indexOf(c) !== -1; })
    .forEach(function (c) { filters.chromosome.add(new Option("chr" + c, c)); });

  // Toggle show more/less genes
  tableElement.addEventListener("click", function (e) {
    var target = e.target;
    if (!target.classList.contains("show-more") && !target.classList.contains("show-less")) return;
    e.preventDefault();
    var genes = JSON.parse(target.dataset.genes);
    var container = document.getElementById("gene-container-" + target.dataset.index);
    var expand = target.classList.contains("show-more");
    container.innerText = expand ? genes.join(", ") : genes.slice(0, 3).join(", ");
    target.innerText = expand ? "less" : "more";
    target.classList.toggle("show-more", !expand);
    target.classList.toggle("show-less", expand);
  });

  // Filters: search text (also on the full gene list) and the select boxes
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    if (settings.nTable !== tableElement) return true;
    var row = settings.aoData[dataIndex].nTr;

    if (filters.chromosome.value && row.dataset.chromosome !== filters.chromosome.value) return false;
    if (filters.type.value && row.dataset.types.split(" ").indexOf(filters.type.value) === -1) return false;
    if (filters.orpha.value && row.dataset.hasOrpha !== filters.orpha.value) return false;

    var input = $("#cnvs-table_filter input").val().toLowerCase().trim();
    if (!input) return true;
    if (data.join(" ").toLowerCase().includes(input)) return true;
    var genes = data[geneColumn].toLowerCase();
    return input.split(/[\s,]+/).filter(Boolean).some(function (term) { return genes.includes(term); });
  });

  $("#cnvs-table_filter input").off().on("keyup change", function () { table.draw(); });
  Object.keys(filters).forEach(function (key) {
    filters[key].addEventListener("change", function () { table.draw(); });
  });
  document.getElementById("filter-reset").addEventListener("click", function () {
    Object.keys(filters).forEach(function (key) { filters[key].value = ""; });
    table.search("").draw();
  });

  drawGenomeOverview(rows, filters, table);
});

// Draw one vertical bar per chromosome and one mark per CNV (GRCh37 coordinates)
function drawGenomeOverview(rows, filters, table) {
  var container = document.getElementById("genome-overview");
  if (!container) return;

  var svgNS = "http://www.w3.org/2000/svg";
  var names = Object.keys(CHROMOSOME_LENGTHS);
  var maxLength = CHROMOSOME_LENGTHS["1"];
  var barHeight = 220, barWidth = 12, step = 34, top = 10, labelSpace = 20;
  var svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", "0 0 " + (names.length * step + 10) + " " + (top + barHeight + labelSpace));
  svg.setAttribute("role", "img");

  function el(tag, attrs) {
    var node = document.createElementNS(svgNS, tag);
    Object.keys(attrs).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    return node;
  }

  names.forEach(function (chrom, i) {
    var x = 10 + i * step;
    var height = barHeight * CHROMOSOME_LENGTHS[chrom] / maxLength;
    var group = el("g", { "class": "chromosome", "data-chromosome": chrom });
    group.appendChild(el("rect", { x: x, y: top, width: barWidth, height: height, rx: 5, "class": "chromosome-bar" }));
    var label = el("text", { x: x + barWidth / 2, y: top + barHeight + 14, "text-anchor": "middle", "class": "chromosome-label" });
    label.textContent = chrom;
    group.appendChild(label);
    group.addEventListener("click", function () {
      filters.chromosome.value = filters.chromosome.value === chrom ? "" : chrom;
      table.draw();
    });
    svg.appendChild(group);
  });

  rows.forEach(function (row) {
    var chrom = row.dataset.chromosome;
    var i = names.indexOf(chrom);
    if (i === -1) return;
    var start = Number(row.dataset.start), end = Number(row.dataset.end);
    var types = row.dataset.types.split(" ").filter(Boolean);
    var isDel = types.indexOf("deletion") !== -1;
    var isDup = types.indexOf("duplication") !== -1 || types.indexOf("triplication") !== -1;
    var kind = isDel && isDup ? "both" : isDel ? "deletion" : isDup ? "duplication" : "none";
    var y = top + barHeight * start / CHROMOSOME_LENGTHS["1"];
    var h = Math.max(2, barHeight * (end - start) / CHROMOSOME_LENGTHS["1"]);
    var link = el("a", { href: row.dataset.url });
    var mark = el("rect", { x: 10 + i * step - 3, y: y, width: barWidth + 6, height: h, "class": "cnv-mark cnv-mark--" + kind });
    var title = el("title", {});
    title.textContent = row.dataset.name + " (chr" + chrom + ":" + start + "-" + end + ")";
    mark.appendChild(title);
    link.appendChild(mark);
    svg.appendChild(link);
  });

  container.appendChild(svg);
}
