"""File system monitoring sensor."""

import os
from pathlib import Path
from typing import Optional

from ghost.sensors.base import BaseSensor


class FileSensor(BaseSensor):
    """Monitors workspace file system activity."""
    
    def __init__(self, workspace_root: Optional[str] = None):
        super().__init__()
        self.workspace_root = Path(workspace_root) if workspace_root else None
    
    def get_context(self) -> str:
        """Get file system context."""
        if not self.workspace_root or not self.workspace_root.exists():
            return ""
        
        try:
            # Count files by type
            file_counts = self._count_files()
            
            context_parts = ["Workspace Activity:"]
            for ext, count in file_counts.items():
                context_parts.append(f"- {ext}: {count} files")
            
            return "\n".join(context_parts)
        except Exception:
            return ""
    
    def _count_files(self) -> dict:
        """Count files by extension."""
        counts = {}
        
        for file_path in self.workspace_root.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix or "no_extension"
                counts[ext] = counts.get(ext, 0) + 1
        
        return counts
    
    def get_name(self) -> str:
        """Get sensor name."""
        return "FileSensor"