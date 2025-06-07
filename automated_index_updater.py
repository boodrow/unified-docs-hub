#!/usr/bin/env python3
"""
Automated Index Updater for Unified Docs Hub
Runs periodic updates to keep documentation fresh and discover new repos
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent))

from unified_docs_hub_server import UnifiedDocsHubServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_indexing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedIndexUpdater:
    def __init__(self):
        self.server = UnifiedDocsHubServer()
        self.last_update_time = {}
        self.config_file = Path(__file__).parent / "auto_index_config.json"
        self.load_config()
    
    def load_config(self):
        """Load configuration for automated indexing"""
        default_config = {
            "update_interval_hours": 24,
            "discover_interval_hours": 168,  # Weekly
            "min_stars_threshold": 3000,
            "discover_count": 30,
            "categories_to_monitor": ["Trading & Finance", "AI/ML", "Cloud/DevOps"],
            "last_curated_update": None,
            "last_discover_update": None
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        
        self.config = default_config
        self.save_config()
    
    def save_config(self):
        """Save configuration state"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)
    
    async def update_curated_repos(self):
        """Update all curated repositories"""
        try:
            logger.info("Starting curated repositories update...")
            result = await self.server.index_repositories(mode="update")
            
            # Parse result
            if "Indexed:" in result:
                indexed_count = int(result.split("Indexed: ")[1].split(" ")[0])
                logger.info(f"Successfully updated {indexed_count} curated repositories")
            
            self.config["last_curated_update"] = datetime.now().isoformat()
            self.save_config()
            
            return True
        except Exception as e:
            logger.error(f"Error updating curated repos: {e}")
            return False
    
    async def discover_new_repos(self):
        """Discover new trending repositories"""
        try:
            logger.info("Discovering new trending repositories...")
            
            # Focus on trading-related queries
            trading_queries = [
                "algorithmic trading",
                "quantitative finance",
                "crypto trading bot",
                "backtesting",
                "trading strategy",
                "options trading",
                "forex trading"
            ]
            
            total_discovered = 0
            
            for query in trading_queries:
                try:
                    logger.info(f"Searching for: {query}")
                    # Note: This would need to be implemented in the server
                    # For now, we'll use the standard discover mode
                    result = await self.server.index_repositories(
                        mode="discover",
                        min_stars=self.config["min_stars_threshold"],
                        count=5  # Limit per query
                    )
                    
                    if "Indexed:" in result:
                        count = int(result.split("Indexed: ")[1].split(" ")[0])
                        total_discovered += count
                    
                    # Small delay between queries
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error discovering repos for '{query}': {e}")
                    continue
            
            logger.info(f"Discovered {total_discovered} new repositories")
            self.config["last_discover_update"] = datetime.now().isoformat()
            self.save_config()
            
            return True
        except Exception as e:
            logger.error(f"Error discovering new repos: {e}")
            return False
    
    async def check_and_update(self):
        """Check if updates are needed and run them"""
        current_time = datetime.now()
        
        # Check if curated update is needed
        if self.config["last_curated_update"]:
            last_curated = datetime.fromisoformat(self.config["last_curated_update"])
            hours_since_update = (current_time - last_curated).total_seconds() / 3600
            
            if hours_since_update >= self.config["update_interval_hours"]:
                logger.info(f"Curated repos update needed ({hours_since_update:.1f} hours since last update)")
                await self.update_curated_repos()
        else:
            # First run
            await self.update_curated_repos()
        
        # Check if discovery is needed
        if self.config["last_discover_update"]:
            last_discover = datetime.fromisoformat(self.config["last_discover_update"])
            hours_since_discover = (current_time - last_discover).total_seconds() / 3600
            
            if hours_since_discover >= self.config["discover_interval_hours"]:
                logger.info(f"Repository discovery needed ({hours_since_discover:.1f} hours since last discovery)")
                await self.discover_new_repos()
        else:
            # First run
            await self.discover_new_repos()
    
    async def run_continuous(self):
        """Run continuous automated indexing"""
        logger.info("Starting automated index updater...")
        logger.info(f"Update interval: {self.config['update_interval_hours']} hours")
        logger.info(f"Discovery interval: {self.config['discover_interval_hours']} hours")
        
        while True:
            try:
                await self.check_and_update()
                
                # Sleep for 1 hour then check again
                logger.info("Sleeping for 1 hour...")
                await asyncio.sleep(3600)
                
            except KeyboardInterrupt:
                logger.info("Shutting down automated indexer...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                # Sleep for 5 minutes on error
                await asyncio.sleep(300)
    
    async def run_once(self):
        """Run a single update cycle"""
        logger.info("Running single update cycle...")
        await self.check_and_update()
        logger.info("Update cycle complete")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated documentation index updater")
    parser.add_argument("--once", action="store_true", help="Run once then exit")
    parser.add_argument("--update-only", action="store_true", help="Only update existing repos")
    parser.add_argument("--discover-only", action="store_true", help="Only discover new repos")
    args = parser.parse_args()
    
    updater = AutomatedIndexUpdater()
    
    if args.update_only:
        await updater.update_curated_repos()
    elif args.discover_only:
        await updater.discover_new_repos()
    elif args.once:
        await updater.run_once()
    else:
        await updater.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())
