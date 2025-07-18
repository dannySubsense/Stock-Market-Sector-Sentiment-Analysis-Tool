"""
Volatility Weight Configuration System - Slice 1A Foundation
Provides configurable volatility multipliers for sector sentiment calculation
Designed for future evolution to dynamic ML-based weighting
"""
from typing import Dict, Any, Optional
from enum import Enum
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class WeightSource(Enum):
    """Source of volatility weights"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    HYBRID = "hybrid"

class VolatilityWeightConfig:
    """
    Configuration manager for sector volatility weights
    Supports static, dynamic, and hybrid weighting strategies
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/volatility_weights.yaml"
        self.weights_source = WeightSource.STATIC
        self.rebalance_frequency = "weekly"
        self.lookback_period = 30  # days
        self.min_weight_change = 0.1
        self.max_change_percent = 0.3
        self.confidence_threshold = 0.7
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or use defaults"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    self._parse_config(config_data)
                logger.info(f"Loaded volatility weights config from {self.config_path}")
            else:
                logger.info("No config file found, using default static weights")
                self._create_default_config()
        except Exception as e:
            logger.warning(f"Error loading config: {e}, using defaults")
            self._create_default_config()
    
    def _parse_config(self, config_data: Dict[str, Any]):
        """Parse configuration data"""
        volatility_config = config_data.get('volatility_weights', {})
        
        # Parse weight source
        source_str = volatility_config.get('source', 'static')
        try:
            self.weights_source = WeightSource(source_str)
        except ValueError:
            logger.warning(f"Invalid weight source: {source_str}, using static")
            self.weights_source = WeightSource.STATIC
        
        # Parse static weights
        self._static_weights = volatility_config.get('static_weights', self._get_default_static_weights())
        
        # Parse dynamic settings
        dynamic_settings = volatility_config.get('dynamic_settings', {})
        self.rebalance_frequency = dynamic_settings.get('rebalance_frequency', 'weekly')
        self.lookback_period = dynamic_settings.get('lookback_period', 30)
        self.max_change_percent = dynamic_settings.get('max_change_percent', 0.3)
        self.confidence_threshold = dynamic_settings.get('confidence_threshold', 0.7)
        
        # Parse hybrid settings
        hybrid_settings = volatility_config.get('hybrid_settings', {})
        self.static_weight_ratio = hybrid_settings.get('static_weight', 0.7)
        self.dynamic_weight_ratio = hybrid_settings.get('dynamic_weight', 0.3)
    
    def _create_default_config(self):
        """Create default configuration"""
        self._static_weights = self._get_default_static_weights()
        self._save_default_config()
    
    def _save_default_config(self):
        """Save default configuration to file"""
        try:
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                'volatility_weights': {
                    'source': 'static',
                    'static_weights': self._static_weights,
                    'dynamic_settings': {
                        'rebalance_frequency': 'weekly',
                        'lookback_period': 30,
                        'max_change_percent': 0.3,
                        'confidence_threshold': 0.7
                    },
                    'hybrid_settings': {
                        'static_weight': 0.7,
                        'dynamic_weight': 0.3
                    }
                }
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            logger.info(f"Created default config file: {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving default config: {e}")
    
    def _get_default_static_weights(self) -> Dict[str, float]:
        """Get default static volatility weights from SDD"""
        return {
            'healthcare': 1.5,      # Highest - FDA catalysts create massive moves
            'technology': 1.3,      # High - AI announcements drive speculation
            'energy': 1.2,          # Medium - Commodity driven
            'consumer_discretionary': 1.2,  # Medium-High - Earnings sensitive
            'financial': 1.1,       # Low-Medium - Regulatory environment
            'industrials': 1.0,     # Neutral - Stable business models
            'materials': 0.9,       # Below neutral - Slow commodity cycles
            'utilities': 0.7        # Lowest - Defensive, stable sector
        }
    
    @property
    def static_weights(self) -> Dict[str, float]:
        """Get current static weights"""
        return self._static_weights.copy()
    
    def get_weight_for_sector(self, sector: str) -> float:
        """Get volatility weight for a specific sector"""
        return self._static_weights.get(sector, 1.0)
    
    def update_static_weight(self, sector: str, new_weight: float):
        """Update static weight for a sector (for testing/fine-tuning)"""
        if sector in self._static_weights:
            old_weight = self._static_weights[sector]
            change_percent = abs(new_weight - old_weight) / old_weight
            
            if change_percent <= self.max_change_percent:
                self._static_weights[sector] = new_weight
                logger.info(f"Updated {sector} weight: {old_weight:.2f} -> {new_weight:.2f}")
                self._save_config()
            else:
                logger.warning(f"Change too large for {sector}: {change_percent:.2%}")
        else:
            logger.warning(f"Unknown sector: {sector}")
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {
                'volatility_weights': {
                    'source': self.weights_source.value,
                    'static_weights': self._static_weights,
                    'dynamic_settings': {
                        'rebalance_frequency': self.rebalance_frequency,
                        'lookback_period': self.lookback_period,
                        'max_change_percent': self.max_change_percent,
                        'confidence_threshold': self.confidence_threshold
                    },
                    'hybrid_settings': {
                        'static_weight': self.static_weight_ratio,
                        'dynamic_weight': self.dynamic_weight_ratio
                    }
                }
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
                
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for monitoring"""
        return {
            'weights_source': self.weights_source.value,
            'static_weights': self._static_weights,
            'rebalance_frequency': self.rebalance_frequency,
            'lookback_period': self.lookback_period,
            'max_change_percent': self.max_change_percent,
            'confidence_threshold': self.confidence_threshold
        }

# Global configuration instance
volatility_config = VolatilityWeightConfig()

def get_volatility_config() -> VolatilityWeightConfig:
    """Get global volatility configuration instance"""
    return volatility_config

def get_static_weights() -> Dict[str, float]:
    """Get current static volatility weights"""
    return volatility_config.static_weights

def get_weight_for_sector(sector: str) -> float:
    """Get volatility weight for a specific sector"""
    return volatility_config.get_weight_for_sector(sector) 