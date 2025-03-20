from typing import Dict, Any
from datetime import datetime

# In-memory session storage
# {session_id: {"processed_har": [...], "timestamp": datetime}}
session_storage: Dict[str, Dict] = {}