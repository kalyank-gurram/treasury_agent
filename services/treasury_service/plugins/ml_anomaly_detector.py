"""Machine learning anomaly detector plugin."""

from typing import List, Dict, Any, Optional
import statistics
from datetime import datetime, timedelta

from .base import DetectorPlugin, PluginMetadata, PluginType
from ..domain.value_objects.treasury import EntityId


class MLAnomalyDetector(DetectorPlugin):
    """Machine learning based anomaly detector."""
    
    def __init__(self):
        self._model_trained = False
        self._baseline_stats = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ml_anomaly_detector",
            version="1.0.0", 
            description="Machine learning anomaly detector using statistical methods",
            plugin_type=PluginType.DETECTOR,
            author="Treasury Agent Team"
        )
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the detector."""
        self.z_threshold = config.get("z_threshold", 3.0)
        self.lookback_days = config.get("lookback_days", 90)
        self.min_samples = config.get("min_samples", 10)
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._baseline_stats.clear()
        self._model_trained = False
    
    async def detect_anomalies(
        self,
        data: List[Dict[str, Any]],
        entity_id: Optional[EntityId] = None
    ) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods."""
        
        if len(data) < self.min_samples:
            return []
        
        # Extract numeric values for analysis
        values = []
        transactions = []
        
        for item in data:
            amount = item.get('amount', 0)
            if isinstance(amount, (int, float)):
                values.append(abs(float(amount)))  # Use absolute values
                transactions.append(item)
        
        if len(values) < self.min_samples:
            return []
        
        # Calculate statistical baseline
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        
        # Store baseline for entity
        entity_key = entity_id.value if entity_id else "global"
        self._baseline_stats[entity_key] = {
            "mean": mean_val,
            "std": std_val,
            "sample_count": len(values)
        }
        
        # Detect anomalies
        anomalies = []
        for i, (value, transaction) in enumerate(zip(values, transactions)):
            if std_val > 0:  # Avoid division by zero
                z_score = abs(value - mean_val) / std_val
                
                if z_score > self.z_threshold:
                    # Check if it's a negative cash flow (more concerning)
                    original_amount = transaction.get('amount', 0)
                    is_outflow = original_amount < 0
                    
                    anomaly = {
                        "id": transaction.get('id', f"tx_{i}"),
                        "date": transaction.get('date', datetime.now().isoformat()),
                        "amount": original_amount,
                        "counterparty": transaction.get('counterparty', 'Unknown'),
                        "z_score": round(z_score, 2),
                        "severity": self._calculate_severity(z_score),
                        "is_outflow": is_outflow,
                        "baseline_mean": round(mean_val, 2),
                        "baseline_std": round(std_val, 2),
                        "anomaly_type": "statistical_outlier",
                        "detection_method": "z_score"
                    }
                    
                    # Add contextual information
                    if is_outflow and z_score > self.z_threshold * 1.5:
                        anomaly["alert_level"] = "HIGH"
                        anomaly["recommendation"] = "Review large outflow immediately"
                    elif z_score > self.z_threshold * 2:
                        anomaly["alert_level"] = "MEDIUM" 
                        anomaly["recommendation"] = "Monitor transaction closely"
                    else:
                        anomaly["alert_level"] = "LOW"
                        anomaly["recommendation"] = "Log for audit trail"
                    
                    anomalies.append(anomaly)
        
        # Sort by severity (highest z-score first)
        anomalies.sort(key=lambda x: x["z_score"], reverse=True)
        
        return anomalies
    
    def _calculate_severity(self, z_score: float) -> str:
        """Calculate severity level based on z-score."""
        if z_score >= 5.0:
            return "CRITICAL"
        elif z_score >= 4.0:
            return "HIGH"
        elif z_score >= 3.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_baseline_stats(self, entity_id: Optional[EntityId] = None) -> Dict[str, Any]:
        """Get baseline statistics for an entity."""
        entity_key = entity_id.value if entity_id else "global"
        return self._baseline_stats.get(entity_key, {})