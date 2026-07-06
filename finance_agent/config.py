"""Configuration management for Fee Forensics."""

import os
from pathlib import Path
from typing import Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class Config:
    """Configuration settings for Fee Forensics."""
    
    def __init__(
        self,
        flag_threshold_abs: float = 25.0,
        flag_threshold_pct: float = 0.05,
        output_dir: str = "reports",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
    ):
        """Initialize configuration.
        
        Args:
            flag_threshold_abs: Absolute threshold for flagging transactions
            flag_threshold_pct: Percentage threshold for flagging
            output_dir: Default output directory for reports
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Optional log file path
        """
        self.flag_threshold_abs = flag_threshold_abs
        self.flag_threshold_pct = flag_threshold_pct
        self.output_dir = output_dir
        self.log_level = log_level
        self.log_file = log_file
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Config instance
            
        Raises:
            ImportError: If PyYAML is not installed
            FileNotFoundError: If config file doesn't exist
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML configuration. "
                "Install it with: pip install pyyaml"
            )
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(
            flag_threshold_abs=data.get("flag_threshold_abs", 25.0),
            flag_threshold_pct=data.get("flag_threshold_pct", 0.05),
            output_dir=data.get("output_dir", "reports"),
            log_level=data.get("log_level", "INFO"),
            log_file=data.get("log_file"),
        )
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.
        
        Returns:
            Config instance
        """
        return cls(
            flag_threshold_abs=float(os.getenv("FF_FLAG_THRESHOLD_ABS", "25.0")),
            flag_threshold_pct=float(os.getenv("FF_FLAG_THRESHOLD_PCT", "0.05")),
            output_dir=os.getenv("FF_OUTPUT_DIR", "reports"),
            log_level=os.getenv("FF_LOG_LEVEL", "INFO"),
            log_file=os.getenv("FF_LOG_FILE"),
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            "flag_threshold_abs": self.flag_threshold_abs,
            "flag_threshold_pct": self.flag_threshold_pct,
            "output_dir": self.output_dir,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }


def get_config(config_path: Optional[Path] = None) -> Config:
    """Get configuration from file, environment, or defaults.
    
    Priority: file > environment > defaults
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Config instance
    """
    if config_path and config_path.exists():
        return Config.from_yaml(config_path)
    
    # Check for default config file
    default_config = Path("fee-forensics.yaml")
    if default_config.exists():
        return Config.from_yaml(default_config)
    
    # Fall back to environment or defaults
    return Config.from_env()
