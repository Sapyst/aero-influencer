"""Compatibilidade pydantic v1 (Android/Chaquopy) e v2 (desktop)."""
from typing import Any, Dict


def model_to_dict(model: Any) -> Dict[str, Any]:
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump()
    return model.dict()
