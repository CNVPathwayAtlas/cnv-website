---
layout: none
---

{%- comment -%}
  Search index for lunr. CNV pages are indexed with their description, Orphanet disorder names,
  ORPHAcodes and gene symbols. Site pages are indexed with their text.
{%- endcomment -%}
{%- assign pages = site.pages | where_exp: 'doc', 'doc.search != false' | where_exp: 'doc', 'doc.title != null' -%}
var store = [
  {%- for doc in site.cnvs -%}
    {%- assign disorder_names = doc.orphadata | map: "name" | compact | join: "; " -%}
    {%- assign orphacodes = doc.orphadata | map: "orphacode" -%}
    {%- assign genes = doc.genes | map: "symbol" -%}
    {
      "title": {{ doc.title | jsonify }},
      "excerpt": {{ doc.description | append: " " | append: disorder_names | strip | truncatewords: 50 | jsonify }},
      "categories": [],
      "tags": {{ genes | concat: orphacodes | jsonify }},
      "url": {{ doc.url | relative_url | jsonify }},
      "teaser": null
    },
  {%- endfor -%}
  {%- for doc in pages -%}
    {
      "title": {{ doc.title | jsonify }},
      "excerpt": {{ doc.content | strip_html | strip_newlines | truncatewords: 50 | jsonify }},
      "categories": [],
      "tags": [],
      "url": {{ doc.url | relative_url | jsonify }},
      "teaser": null
    }{%- unless forloop.last -%},{%- endunless -%}
  {%- endfor -%}
]
