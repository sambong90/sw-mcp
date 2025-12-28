"""Test canonical JSON hashing"""

import pytest
from src.sw_mcp.swarfarm.hashing import canonicalize_json, compute_hash


def test_canonicalize_json_stable_order():
    """Test that canonical JSON has stable key order"""
    obj1 = {"b": 2, "a": 1, "c": 3}
    obj2 = {"a": 1, "b": 2, "c": 3}
    
    canonical1 = canonicalize_json(obj1)
    canonical2 = canonicalize_json(obj2)
    
    assert canonical1 == canonical2
    assert canonical1 == '{"a":1,"b":2,"c":3}'


def test_compute_hash_stable():
    """Test that hash is stable across key order"""
    obj1 = {"b": 2, "a": 1, "c": 3}
    obj2 = {"a": 1, "b": 2, "c": 3}
    
    hash1 = compute_hash(obj1)
    hash2 = compute_hash(obj2)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex


def test_compute_hash_different_objects():
    """Test that different objects have different hashes"""
    obj1 = {"a": 1, "b": 2}
    obj2 = {"a": 1, "b": 3}
    
    hash1 = compute_hash(obj1)
    hash2 = compute_hash(obj2)
    
    assert hash1 != hash2


