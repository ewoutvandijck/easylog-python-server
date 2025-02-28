from typing import Any


def object_to_formatted_text(obj: Any) -> str:
    if isinstance(obj, dict):
        return "\n".join([f"{k}: {object_to_formatted_text(v)}" for k, v in obj.items()])
    elif isinstance(obj, list):
        return "\n".join([object_to_formatted_text(item) for item in obj])
    else:
        return str(obj)
