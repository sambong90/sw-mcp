"""File storage for SWEX JSON imports"""

import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class StorageManager:
    """Manages storage of imported JSON files"""
    
    def __init__(self, storage_dir: str = "storage/imports"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_json(self, json_data: Dict[str, Any]) -> str:
        """
        Save JSON data to file and return relative path
        
        Args:
            json_data: SWEX JSON dictionary
            
        Returns:
            Relative path to saved file
        """
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"import_{timestamp}_{unique_id}.json"
        filepath = self.storage_dir / filename
        
        # Save JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # Return relative path
        return str(filepath.relative_to(Path.cwd()))
    
    def load_json(self, filepath: str) -> Dict[str, Any]:
        """
        Load JSON data from file
        
        Args:
            filepath: Relative path to JSON file
            
        Returns:
            JSON dictionary
        """
        full_path = Path(filepath)
        if not full_path.is_absolute():
            full_path = Path.cwd() / filepath
        
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def delete_json(self, filepath: str) -> bool:
        """
        Delete JSON file
        
        Args:
            filepath: Relative path to JSON file
            
        Returns:
            True if deleted, False if not found
        """
        full_path = Path(filepath)
        if not full_path.is_absolute():
            full_path = Path.cwd() / filepath
        
        if full_path.exists():
            full_path.unlink()
            return True
        return False


# Global storage manager instance
storage_manager = StorageManager()

