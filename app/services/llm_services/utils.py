"""Utility functions for LLM services."""

import json
import re
from typing import Any, Dict, List, Tuple

from .constants import FUNC_RE, ARG_RE, FUNC_CALL_PATTERN


def coerce_value(v: str) -> Any:
    """Convert string value to appropriate type (int/float/bool/None/JSON)."""
    s = v.strip()

    # Boolean
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False

    # Null/none
    if low in ("null", "none"):
        return None

    # Integer
    if re.fullmatch(r"[+-]?\d+", s):
        try:
            return int(s)
        except Exception:
            pass

    # Float
    if re.fullmatch(r"[+-]?\d+\.\d+", s):
        try:
            return float(s)
        except Exception:
            pass

    # JSON object/array
    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        try:
            return json.loads(s)
        except Exception:
            pass

    # Default to string
    return s


def parse_func_call(s: str) -> Tuple[str, Dict[str, Any]]:
    """Parse function call string into name and arguments."""
    m = FUNC_RE.match(s.strip())
    if not m:
        raise ValueError(f"Bad func_call format: {s}")
    
    name = m.group("name").strip()
    args = m.group("args") or ""
    kwargs: Dict[str, Any] = {}
    
    for kv in ARG_RE.finditer(args):
        k = kv.group("k")
        v = kv.group("v")

        # Remove outer quotes if present
        if (len(v) >= 2) and ((v.startswith('"') and v.endswith('"')) or 
                              (v.startswith("'") and v.endswith("'"))):
            v = v[1:-1]

        kwargs[k] = coerce_value(v)

    return name, kwargs


def extract_func_calls(text: str) -> List[str]:
    """Extract function calls from text."""
    return [m.group(1).strip() for m in FUNC_CALL_PATTERN.finditer(text)]