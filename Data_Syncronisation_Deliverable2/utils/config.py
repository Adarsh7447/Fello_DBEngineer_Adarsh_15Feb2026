"""
Configuration Management
Handles environment variables and configuration settings
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration management
    """
    
    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize configuration manager
        
        Args:
            env_file: Path to .env file (optional)
        """
        if env_file and env_file.exists():
            load_dotenv(dotenv_path=env_file)
            logger.info(f"Loaded environment from: {env_file}")
        else:
            # Try to find .env in common locations
            possible_locations = [
                Path.cwd() / '.env',
                Path(__file__).parent.parent / '.env',
                Path(__file__).parent.parent / 'etl' / '.env',
            ]
            
            for location in possible_locations:
                if location.exists():
                    load_dotenv(dotenv_path=location)
                    logger.info(f"Loaded environment from: {location}")
                    break
            else:
                logger.warning("No .env file found in common locations")
    
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        url = os.getenv('DATABASE_URL')
        if not url:
            raise ValueError("DATABASE_URL not set in environment")
        return url
    
    @property
    def supabase_url(self) -> Optional[str]:
        """Get Supabase project URL"""
        return os.getenv('SUPABASE_URL')
    
    @property
    def supabase_key(self) -> Optional[str]:
        """Get Supabase service role key"""
        return os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    @property
    def log_level(self) -> str:
        """Get logging level"""
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def batch_size(self) -> int:
        """Get batch processing size"""
        return int(os.getenv('BATCH_SIZE', '1000'))
    
    @property
    def enable_rls(self) -> bool:
        """Check if RLS should be enabled"""
        return os.getenv('ENABLE_RLS', 'true').lower() == 'true'
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return os.getenv(key, default)
    
    def get_all(self) -> Dict[str, str]:
        """
        Get all environment variables
        
        Returns:
            Dictionary of all environment variables
        """
        return dict(os.environ)
    
    def validate_required_vars(self, required_vars: list) -> bool:
        """
        Validate that required environment variables are set
        
        Args:
            required_vars: List of required variable names
            
        Returns:
            True if all required vars are set, False otherwise
        """
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            logger.error(f"Missing required environment variables: {', '.join(missing)}")
            return False
        
        logger.info("All required environment variables are set")
        return True
