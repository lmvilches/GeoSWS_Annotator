# GeoSWS_Annotator
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zenodo](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)


A reconstructed and extensible codebase implementing a semantic annotation pipeline for geospatial services, including:

* RESTful Web APIs, and
* OGC WFS (Web Feature Service).

The system extracts parameters, proposes ontology candidates, enriches terms using external resources, retrieves SPARQL evidence, and exports results in JSON and RDF/Turtle.

This reconstruction aims for reproducibility, extensibility, and strong alignment with FAIR principles.

Team: Víctor Saquicela | Luis M. Vilches-Blázquez | Oscar Corcho

If you want to cite GeoSWS_Annotator in a scientific paper or technical report, you can use the following articles: 

* Saquicela, V., Vilches-Blázquez, L. M., & Corcho, O. (2012). Adding semantic annotations into (geospatial) RESTful services. International Journal on Semantic Web and Information Systems (IJSWIS), 8(2), 51–71. https://doi.org/10.4018/jswis.2012040103

* Saquicela, V., Vilches-Blázquez, L. M., Freire, R., & Corcho, O. (2022). Annotating OGC web feature services automatically for generating geospatial knowledge graphs. Transactions in GIS, 26, 505–541. https://doi.org/10.1111/tgis.12863 

# Table of Contents

* Features
* Repository-structure
* Requirements
* Installation
* Quick-usage-cli
* semantic-annotation-pipeline
* configuration-examples
* output-formats--interoperability
* reproducible-tests


# Features

* Extraction of inputs/outputs from REST and OGC WFS services.
* Hybrid ontology matching (exact + similarity metrics).
* Semantic enrichment using external suggestion/synonym providers.
* Evidence retrieval using SPARQL queries.
* Export to JSON and RDF/Turtle.
* Built‑in SQLite cache for SPARQL and external calls.

# Repository Structure

```
geosws_annotator/
│ README.md
│ pyproject.toml
│ requirements.txt
│ LICENSE
│ examples/
│   config_dbpedia_geonames.json
│   config_wfs.json
│   config_rest.json
│ geosws_annotator/
│   __init__.py
│   cli.py
│   config.py
│   models.py
│   utils/
│   ontology/
│   annotate/
│   rest/
│   wfs/
│   sparql/
│   external/
```

---

## **Requirements**

- Python **3.10+**  
- `pip` / `virtualenv`  
- Internet connection for SPARQL and external enrichment  
- Python dependencies (via `requirements.txt`):  
  - `requests`, `lxml`, `rdflib`, etc.  


---

## **Installation**

```bash
git clone <repository-url>
cd geosws_annotator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
---

## **Validate**

python -m geosws_annotator.cli --help

---


# Quick Usage (CLI)
* Build ontology index

```python -m geosws_annotator.cli build-ontology-index \
  --config examples/config_dbpedia_geonames.json \
  --out data/ontology_index.json
```

---

* Annotate a WFS service
```python -m geosws_annotator.cli annotate-wfs \
  --config examples/config_wfs.json \
  --out out_wfs/
```

---

* Annotate a REST service
```python -m geosws_annotator.cli annotate-rest \
  --config examples/config_rest.json \
  --out out_rest/
```

---

# Semantic Annotation Pipeline
The system processes parameters in six stages:

1. Special parameter detection (pagination, bbox, lat/lng…).
2. Initial matching (exact + similarity).
3. SPARQL instance retrieval for ontology candidates.
4. Enrichment from external suggestion/synonym services.
5. Re-matching using enriched terms.
6. Export to JSON or Turtle (RDF).


---

# Configuration Examples

WFS Configuration Example

```{
  "sparql_endpoints": [
    {"name": "dbpedia", "url": "https://dbpedia.org/sparql"},
    {"name": "geonames", "url": "http://sparql.geonames.org/sparql"}
  ],
  "ontology_index": {
    "index_path": "data/ontology_index.json"
  },
  "external_resources": {
    "enable_suggestions": true,
    "enable_synonyms": true
  },
  "matching": {
    "jaro_threshold": 0.92,
    "levenshtein_ratio_threshold": 0.85
  },
  "cache_sqlite_path": "data/cache.sqlite",
  "instances_limit": 50,
  "http_timeout_s": 25,
  "wfs_targets": [
    {
      "base_url": "http://example.com/geoserver/wfs",
      "version": "1.1.0"
    }
  ]
}
```

---

REST Configuration Example

```{
  "sparql_endpoints": [
    {"name": "dbpedia", "url": "https://dbpedia.org/sparql"}
  ],
  "ontology_index": {
    "index_path": "data/ontology_index.json"
  },
  "external_resources": {
    "enable_suggestions": true,
    "enable_synonyms": true
  },
  "matching": {
    "jaro_threshold": 0.92,
    "levenshtein_ratio_threshold": 0.85
  },
  "cache_sqlite_path": "data/cache.sqlite",
  "instances_limit": 50,
  "http_timeout_s": 25,
  "rest_targets": [
    {
      "base_url": "https://example.com/api/items"
    }
  ]
}
```

---

# Output Formats & Interoperability
* JSON detailed report of candidates, evidence, enrichment, validation flags.
* Turtle (RDF/Turtle) generated via rdflib.
* Supports:

1. OGC WFS (1.0.0 / 1.1.0 / 2.0.0)
2. REST JSON/XML
3. SPARQL 1.1
4. RDF/OWL ontologies

---

# Reproducible Tests

1. Installation Test

```
python -m geosws_annotator.cli --help
```

---

2. Test: Build Ontology Index

```python -m geosws_annotator.cli build-ontology-index \
  --config examples/config_dbpedia_geonames.json \
  --out data/ontology_index.json
```
Expected result: A new file data/ontology_index.json is created.

---

3. Test: Annotate a WFS (smoke test)

```python -m geosws_annotator.cli annotate-wfs \
  --config examples/config_wfs.json \
  --out out_wfs/
```
Expected output:

out_wfs/wfs_1/service.json
out_wfs/wfs_1/service.ttl (if RDF enabled)

---

4. Test: Annotate a REST Endpoint
   
```python -m geosws_annotator.cli annotate-rest \
  --config examples/config_rest.json \
  --out out_rest/
```
Expected output:

out_rest/rest_1/service.json
out_rest/rest_1/service.ttl

---

5. Quick Inspection of Results

```
python -c "import json;print(json.dumps(json.load(open('out_wfs/wfs_1/service.json')), indent=2, ensure_ascii=False)[:2000])"
```
Inspect fields: special_type, ontology_candidates, suggestions, validated.

---






