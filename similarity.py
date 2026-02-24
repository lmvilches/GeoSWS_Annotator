from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from .config import PipelineConfig, SparqlEndpointConfig, OntologyIndexConfig, ExternalResourcesConfig, MatchingConfig
from .ontology.index import OntologyIndex
from .sparql.client import SparqlClient
from .utils.cache import SqliteCache
from .annotate.pipeline import AnnotationPipeline
from .rest.analyzer import analyze_rest_endpoint
from .wfs.analyzer import analyze_wfs
from .export.json_export import export_service_json
from .export.rdf_export import export_service_turtle


def _pipeline_config_from_json(cfg: Dict[str, Any]) -> PipelineConfig:
    endpoints = [SparqlEndpointConfig(**x) for x in cfg.get("sparql_endpoints", [])]
    if not endpoints:
        raise ValueError("config must include at least one sparql_endpoints entry")

    ontology_index = OntologyIndexConfig(**cfg.get("ontology_index", {}))
    external_resources = ExternalResourcesConfig(**cfg.get("external_resources", {}))
    matching = MatchingConfig(**cfg.get("matching", {}))

    return PipelineConfig(
        sparql_endpoints=endpoints,
        ontology_index=ontology_index,
        external_resources=external_resources,
        matching=matching,
        cache_sqlite_path=cfg.get("cache_sqlite_path", "data/cache.sqlite"),
        instances_limit=int(cfg.get("instances_limit", 50)),
        validation_trials=int(cfg.get("validation_trials", 20)),
        http_timeout_s=float(cfg.get("http_timeout_s", 25.0)),
    )


def cmd_build_ontology_index(args: argparse.Namespace) -> int:
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    p = _pipeline_config_from_json(cfg)
    os.makedirs(os.path.dirname(p.cache_sqlite_path) or ".", exist_ok=True)
    cache = SqliteCache(p.cache_sqlite_path)
    client = SparqlClient(p.sparql_endpoints[0].url, cache=cache, timeout_s=p.sparql_endpoints[0].timeout_s, user_agent=p.sparql_endpoints[0].user_agent)
    idx = OntologyIndex.build_from_sparql(client=client, languages=p.ontology_index.languages, limit=p.ontology_index.limit_per_type)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    idx.to_json(args.out)
    print(f"Ontology index written to: {args.out} (elements={len(idx.elements)})")
    return 0


def cmd_annotate_rest(args: argparse.Namespace) -> int:
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    p = _pipeline_config_from_json(cfg)
    pipeline = AnnotationPipeline(p)

    targets = cfg.get("rest_targets", [])
    if not targets:
        raise ValueError("config must include rest_targets: [{url, method?, input_hints?}]" )

    os.makedirs(args.out, exist_ok=True)

    for i, t in enumerate(targets, start=1):
        svc = analyze_rest_endpoint(t["url"], method=t.get("method", "GET"), timeout_s=p.http_timeout_s)
        # annotate parameters of first operation (heuristic)
        op = svc.operations[0]
        pipeline.annotate_parameters(op.inputs + op.outputs)
        pipeline.validate_rest_inputs(op.url, op.inputs)

        out_dir = os.path.join(args.out, f"rest_{i}")
        export_service_json(svc, out_dir, name="service.json")
        export_service_turtle(svc, out_dir, name="service.ttl")
        print(f"Annotated REST service saved in: {out_dir}")
    return 0


def cmd_annotate_wfs(args: argparse.Namespace) -> int:
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    p = _pipeline_config_from_json(cfg)
    pipeline = AnnotationPipeline(p)

    targets = cfg.get("wfs_targets", [])
    if not targets:
        raise ValueError("config must include wfs_targets: [{base_url, version?}]" )

    os.makedirs(args.out, exist_ok=True)

    for i, t in enumerate(targets, start=1):
        svc = analyze_wfs(t["base_url"], version=t.get("version", "1.1.0"), timeout_s=p.http_timeout_s)
        # annotate all DescribeFeatureType output parameters
        for op in svc.operations:
            if op.name.startswith("DescribeFeatureType:"):
                pipeline.annotate_parameters(op.outputs)
        out_dir = os.path.join(args.out, f"wfs_{i}")
        export_service_json(svc, out_dir, name="service.json")
        export_service_turtle(svc, out_dir, name="service.ttl")
        print(f"Annotated WFS service saved in: {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="geosws-annotator", description="Semantic annotation pipeline for RESTful and WFS services.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_idx = sub.add_parser("build-ontology-index", help="Build local JSON ontology index from SPARQL endpoint.")
    p_idx.add_argument("--config", required=True)
    p_idx.add_argument("--out", required=True)
    p_idx.set_defaults(func=cmd_build_ontology_index)

    p_rest = sub.add_parser("annotate-rest", help="Annotate REST endpoints.")
    p_rest.add_argument("--config", required=True)
    p_rest.add_argument("--out", required=True)
    p_rest.set_defaults(func=cmd_annotate_rest)

    p_wfs = sub.add_parser("annotate-wfs", help="Annotate WFS services.")
    p_wfs.add_argument("--config", required=True)
    p_wfs.add_argument("--out", required=True)
    p_wfs.set_defaults(func=cmd_annotate_wfs)

    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    rc = args.func(args)
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
