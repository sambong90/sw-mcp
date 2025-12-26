"""Ruleset loader from DB or file"""

import json
from typing import Optional, Dict
from pathlib import Path
from .schema import Ruleset
from ..db.repo import SwarfarmRepository
from ..db.models import RulesetVersion


def load_ruleset_from_json(file_path: str) -> Ruleset:
    """Load ruleset from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return Ruleset(**data)


def load_ruleset_from_db(repo: SwarfarmRepository, version_tag: Optional[str] = None) -> Optional[Ruleset]:
    """
    Load ruleset from DB
    
    Args:
        repo: SwarfarmRepository instance
        version_tag: Version tag (None = latest)
    
    Returns:
        Ruleset or None if not found
    """
    if version_tag:
        version = repo.session.query(RulesetVersion).filter(
            RulesetVersion.version_tag == version_tag
        ).first()
    else:
        # Get latest by created_at
        version = repo.session.query(RulesetVersion).order_by(
            RulesetVersion.created_at.desc()
        ).first()
    
    if not version:
        return None
    
    return Ruleset(**json.loads(version.rules_json))


def save_ruleset_to_db(repo: SwarfarmRepository, ruleset: Ruleset, sources_json: Optional[Dict] = None):
    """
    Save ruleset to DB
    
    Args:
        repo: SwarfarmRepository instance
        ruleset: Ruleset to save
        sources_json: Optional sources metadata
    """
    from datetime import datetime
    
    # Check if version exists
    existing = repo.session.query(RulesetVersion).filter(
        RulesetVersion.version_tag == ruleset.version
    ).first()
    
    rules_json = ruleset.model_dump_json()
    sources_json_str = json.dumps(sources_json) if sources_json else None
    
    if existing:
        # Update
        existing.effective_date = ruleset.metadata.effective_date
        existing.rules_json = rules_json
        existing.sources_json = sources_json_str
        existing.created_at = datetime.utcnow()
    else:
        # Insert
        new_version = RulesetVersion(
            version_tag=ruleset.version,
            effective_date=ruleset.metadata.effective_date,
            rules_json=rules_json,
            sources_json=sources_json_str,
        )
        repo.session.add(new_version)
    
    repo.commit()

