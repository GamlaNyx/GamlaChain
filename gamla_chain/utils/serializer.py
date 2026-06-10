import json
from dataclasses import asdict, is_dataclass
from typing import Any


class ChainEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def to_json(obj: Any, indent: int | None = None) -> str:
    return json.dumps(obj, cls=ChainEncoder, indent=indent)
