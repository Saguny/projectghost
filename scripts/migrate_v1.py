"""Migration script for upgrading from v1 to current version."""

import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_emotional_state():
    """Migrate emotional state format if needed."""
    state_file = Path("data/emotional_state.json")
    
    if not state_file.exists():
        logger.info("No emotional state file found, skipping migration")
        return
    
    try:
        with open(state_file) as f:
            data = json.load(f)
        
        # Check if migration needed
        if "version" in data and data["version"] >= 2:
            logger.info("Emotional state already migrated")
            return
        
        # Add version and backup old data
        data["version"] = 2
        data["migrated_at"] = datetime.utcnow().isoformat()
        
        # Save migrated data
        backup_file = state_file.with_suffix('.json.backup')
        state_file.rename(backup_file)
        
        with open(state_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Emotional state migrated successfully. Backup: {backup_file}")
        
    except Exception as e:
        logger.error(f"Failed to migrate emotional state: {e}")


def migrate_memory_snapshots():
    """Migrate memory snapshot format if needed."""
    snapshot_dir = Path("data/memory_snapshots")
    
    if not snapshot_dir.exists():
        logger.info("No snapshot directory found, skipping migration")
        return
    
    migrated_count = 0
    
    for snapshot_file in snapshot_dir.glob("snapshot_*.json"):
        try:
            with open(snapshot_file) as f:
                data = json.load(f)
            
            # Check if migration needed
            if "format_version" in data:
                continue
            
            # Add format version
            data["format_version"] = 2
            data["migrated_at"] = datetime.utcnow().isoformat()
            
            with open(snapshot_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            migrated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to migrate {snapshot_file}: {e}")
    
    if migrated_count > 0:
        logger.info(f"Migrated {migrated_count} memory snapshots")
    else:
        logger.info("No snapshots needed migration")


def main():
    """Run all migrations."""
    logger.info("Starting Project Ghost v1 migration")
    logger.info("=" * 50)
    
    migrate_emotional_state()
    migrate_memory_snapshots()
    
    logger.info("=" * 50)
    logger.info("Migration complete!")


if __name__ == "__main__":
    main()