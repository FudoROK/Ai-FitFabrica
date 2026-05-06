from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel


@dataclass(frozen=True)
class SchemaEntry:
    schema_model: type[BaseModel]
    schema_version: str
    postprocess: Callable[[dict], dict] | None = None


_REGISTRY: dict[str, SchemaEntry] = {}


def register_schema(
    task_name: str,
    schema_model: type[BaseModel],
    schema_version: str = "v1",
    postprocess: Callable[[dict], dict] | None = None,
) -> None:
    _REGISTRY[task_name] = SchemaEntry(
        schema_model=schema_model,
        schema_version=schema_version,
        postprocess=postprocess,
    )


def get_schema(task_name: str) -> tuple[type[BaseModel], str, Callable[[dict], dict] | None]:
    if task_name not in _REGISTRY:
        raise KeyError(f"schema_not_registered:{task_name}")
    entry = _REGISTRY[task_name]
    return entry.schema_model, entry.schema_version, entry.postprocess
