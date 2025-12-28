"""In-memory state for MCP server"""

from typing import List, Optional, Dict, Any
from sw_core.types import Rune
from sw_core.api import run_search


class ServerState:
    """MCP server state (singleton)"""
    _instance: Optional['ServerState'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.runes: List[Rune] = []
        self.loaded_json_path: Optional[str] = None
        self.recent_results: List[Dict[str, Any]] = []
        self._initialized = True
    
    def load_runes(self, runes: List[Rune], json_path: Optional[str] = None):
        """Load runes into state"""
        self.runes = runes
        self.loaded_json_path = json_path
        self.recent_results = []
    
    def reset(self):
        """Reset all state"""
        self.runes = []
        self.loaded_json_path = None
        self.recent_results = []
    
    def add_results(self, results: List[Dict[str, Any]]):
        """Add search results to recent history"""
        self.recent_results = results


# Global state instance
_state = ServerState()


def get_state() -> ServerState:
    """Get global server state"""
    return _state
