"""Canonical JSON hashing for change detection"""

import json
import hashlib
from typing import Any, Dict


def canonicalize_json(obj: Any) -> str:
    """
    Canonical JSON representation (stable key order, no whitespace)
    
    Args:
        obj: Python object to canonicalize
    
    Returns:
        Canonical JSON string
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def compute_hash(payload: Any) -> str:
    """
    Compute SHA256 hash of canonical JSON
    
    Args:
        payload: Python object
    
    Returns:
        SHA256 hex digest
    """
    canonical = canonicalize_json(payload)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def compute_hash_from_json(json_str: str) -> str:
    """
    Compute hash from JSON string (parse first to ensure canonical form)
    
    Args:
        json_str: JSON string
    
    Returns:
        SHA256 hex digest
    """
    obj = json.loads(json_str)
    return compute_hash(obj)

