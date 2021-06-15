# -*- coding:utf-8 -*-

import json

from typing import Dict, Generator, Tuple, Any

try:
    from apex import amp  # noqa: F401

    _has_apex = True
except ImportError:
    _has_apex = False

try:
    import torch_xla.core.xla_model as xm  # noqa: F401

    _torch_tpu_available = True  # pylint: disable=
except ImportError:
    _torch_tpu_available = False


def is_apex_available():
    return _has_apex


def is_torch_tpu_available():
    return _torch_tpu_available


class JsonlReader:
    def __init__(self, fname: str):
        self.fname = fname
    
    def __iter__(self) -> Generator[Any, None, None]:
        with open(self.fname, encoding="utf-8", errors="ignore") as rf:
            for jsonl in rf:
                jsonl = jsonl.strip()
                if not jsonl:
                    continue
                yield json.loads(jsonl)


class TriplesReader:
    def __init__(self, fname: str):
        self.fname = fname
    
    def __iter__(self) -> Generator[Tuple[str, str, str], None, None]:
        with open(self.fname, encoding="utf-8", errors="ignore") as rf:
            for tsvl in rf:
                tsvl = tsvl.strip()
                if not tsvl:
                    continue
                yield tsvl.split("\t")


def read_relations(relations_file: str, with_dir: bool = False) -> Dict[str, int]:
    relation2idx = dict()
    idx = 0
    with open(relations_file) as rf:
        for relation in rf:
            relation = relation.strip()
            if not relation:
                continue
            if with_dir and relation != "NA":
                relation2idx[relation+"(e1,e2)"] = idx
                idx += 1
                relation2idx[relation+"(e2,e1)"] = idx
                idx += 1
            else:
                relation2idx[relation] = idx
                idx += 1
    return relation2idx


def read_entities(entities_file: str) -> Dict[str, int]:
    entity2idx = dict()
    idx = 0
    with open(entities_file) as rf:
        for entity in rf:
            entity = entity.strip()
            if not entity:
                continue
            entity2idx[entity] = idx
            idx += 1
    return entity2idx
