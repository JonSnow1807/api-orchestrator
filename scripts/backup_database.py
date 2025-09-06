#!/usr/bin/env python3
"""
Database backup script for StreamAPI
Performs automated backups with rotation and optional cloud upload
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import gzip
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    """Handles database backup operations"""
    
    def __init__(self):
        self.backup_dir = Path("/app/backups")
        if not os.path.exists('/app'):
            # Local development
            self.backup_dir = Path("./backups")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = 7
        
    def get_database_url(self):
        """Get database URL from environment"""
        db_url = os.getenv("DATABASE_URL", "")
        
        # Fix Railway PostgreSQL URL format
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        if not db_url or "postgresql" not in db_url:
            logger.error("PostgreSQL DATABASE_URL not found")
            return None
            
        return db_url
    
    def create_backup(self):
        """Create database backup"""
        db_url = self.get_database_url()
        if not db_url:
            return False
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_{timestamp}.sql"
        compressed_file = self.backup_dir / f"backup_{timestamp}.sql.gz"
        
        try:
            # Create SQL dump
            logger.info(f"Creating backup: {backup_file}")
            result = subprocess.run(
                ["pg_dump", db_url],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Write to file
            with open(backup_file, 'w') as f:
                f.write(result.stdout)
            
            # Compress the backup
            logger.info(f"Compressing backup to: {compressed_file}")
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            backup_file.unlink()
            
            # Get file size
            size_mb = compressed_file.stat().st_size / (1024 * 1024)
            logger.info(f"Backup completed: {compressed_file} ({size_mb:.2f} MB)")
            
            return str(compressed_file)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Backup error: {str(e)}")
            return False
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_file in self.backup_dir.glob("backup_*.sql.gz"):
            # Parse timestamp from filename
            try:
                timestamp_str = backup_file.stem.replace("backup_", "").replace(".sql", "")
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    logger.info(f"Removing old backup: {backup_file}")
                    backup_file.unlink()
            except Exception as e:
                logger.warning(f"Could not process {backup_file}: {e}")
    
    def list_backups(self):
        """List all available backups"""
        backups = []
        for backup_file in sorted(self.backup_dir.glob("backup_*.sql.gz")):
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            timestamp_str = backup_file.stem.replace("backup_", "").replace(".sql", "")
            
            try:
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                backups.append({
                    "file": str(backup_file),
                    "date": file_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "size_mb": f"{size_mb:.2f}",
                    "age_days": (datetime.now() - file_date).days
                })
            except:
                continue
        
        return backups
    
    def restore_backup(self, backup_file):
        """Restore database from backup file"""
        db_url = self.get_database_url()
        if not db_url:
            return False
        
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            # Decompress if needed
            if backup_path.suffix == '.gz':
                logger.info(f"Decompressing backup: {backup_path}")
                sql_file = backup_path.with_suffix('')
                
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(sql_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                sql_file = backup_path
            
            # Restore database
            logger.info(f"Restoring database from: {sql_file}")
            with open(sql_file, 'r') as f:
                result = subprocess.run(
                    ["psql", db_url],
                    stdin=f,
                    capture_output=True,
                    text=True,
                    check=True
                )
            
            # Clean up decompressed file if we created it
            if backup_path.suffix == '.gz' and sql_file.exists():
                sql_file.unlink()
            
            logger.info("Database restored successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Restore error: {str(e)}")
            return False
    
    def get_database_stats(self):
        """Get database statistics"""
        db_url = self.get_database_url()
        if not db_url:
            return None
        
        try:
            # Get database size
            size_query = "SELECT pg_database_size(current_database());"
            result = subprocess.run(
                ["psql", db_url, "-t", "-c", size_query],
                capture_output=True,
                text=True,
                check=True
            )
            size_bytes = int(result.stdout.strip())
            size_mb = size_bytes / (1024 * 1024)
            
            # Get table counts
            count_query = """
            SELECT 
                (SELECT COUNT(*) FROM users) as users,
                (SELECT COUNT(*) FROM projects) as projects,
                (SELECT COUNT(*) FROM apis) as apis,
                (SELECT COUNT(*) FROM api_tests) as tests;
            """
            result = subprocess.run(
                ["psql", db_url, "-t", "-c", count_query],
                capture_output=True,
                text=True,
                check=True
            )
            
            counts = result.stdout.strip().split('|')
            
            return {
                "size_mb": f"{size_mb:.2f}",
                "users": int(counts[0].strip()) if len(counts) > 0 else 0,
                "projects": int(counts[1].strip()) if len(counts) > 1 else 0,
                "apis": int(counts[2].strip()) if len(counts) > 2 else 0,
                "tests": int(counts[3].strip()) if len(counts) > 3 else 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return None

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='StreamAPI Database Backup Tool')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'cleanup', 'stats'],
                       help='Action to perform')
    parser.add_argument('--file', help='Backup file for restore operation')
    
    args = parser.parse_args()
    
    backup = DatabaseBackup()
    
    if args.action == 'backup':
        logger.info("=== Starting Database Backup ===")
        backup_file = backup.create_backup()
        if backup_file:
            backup.cleanup_old_backups()
            logger.info("✅ Backup completed successfully")
        else:
            logger.error("❌ Backup failed")
            sys.exit(1)
            
    elif args.action == 'restore':
        if not args.file:
            logger.error("Please specify backup file with --file")
            sys.exit(1)
        
        logger.info("=== Starting Database Restore ===")
        if backup.restore_backup(args.file):
            logger.info("✅ Restore completed successfully")
        else:
            logger.error("❌ Restore failed")
            sys.exit(1)
            
    elif args.action == 'list':
        logger.info("=== Available Backups ===")
        backups = backup.list_backups()
        if not backups:
            logger.info("No backups found")
        else:
            for b in backups:
                logger.info(f"📁 {b['date']} - {b['size_mb']} MB - {b['age_days']} days old")
                logger.info(f"   {b['file']}")
                
    elif args.action == 'cleanup':
        logger.info("=== Cleaning Old Backups ===")
        backup.cleanup_old_backups()
        logger.info("✅ Cleanup completed")
        
    elif args.action == 'stats':
        logger.info("=== Database Statistics ===")
        stats = backup.get_database_stats()
        if stats:
            logger.info(f"📊 Database size: {stats['size_mb']} MB")
            logger.info(f"👥 Users: {stats['users']}")
            logger.info(f"📁 Projects: {stats['projects']}")
            logger.info(f"🔌 APIs: {stats['apis']}")
            logger.info(f"🧪 Tests: {stats['tests']}")
        else:
            logger.error("Could not retrieve database statistics")

if __name__ == "__main__":
    main()