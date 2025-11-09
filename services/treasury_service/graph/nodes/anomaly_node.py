"""Enhanced anomaly detection node for Treasury Agent."""

import pandas as pd
from ...detectors.anomaly import TreasuryAnomalyDetector, outflow_anomalies
from ..types import AgentState
from .utils import api
from ...infrastructure.observability import trace_operation, monitor_performance


def _process_anomaly_record(row):
    """Process a single anomaly record for JSON serialization."""
    anomaly_record = {
        "date": str(row['date']),
        "value": float(row['value']),
        "method": row['method'],
        "severity": row['severity'],
        "description": row['description']
    }
    
    # Add method-specific fields
    if 'z_score' in row and pd.notna(row['z_score']):
        anomaly_record['z_score'] = float(row['z_score'])
    if 'ml_score' in row and pd.notna(row['ml_score']):
        anomaly_record['ml_score'] = float(row['ml_score'])
    if 'pattern_length' in row and pd.notna(row['pattern_length']):
        anomaly_record['pattern_length'] = int(row['pattern_length'])
        
    return anomaly_record


def _create_anomaly_result(anomalies_df, hist):
    """Create formatted result for successful anomaly detection."""
    if len(anomalies_df) == 0:
        return {
            "anomalies": [],
            "summary": {
                "total_anomalies": 0,
                "message": "No significant anomalies detected in the analysis period"
            },
            "analysis_period": {
                "start_date": str(hist.index[0]),
                "end_date": str(hist.index[-1]),
                "data_points": len(hist)
            }
        }
    
    # Process anomalies
    anomalies_list = [_process_anomaly_record(row) for _, row in anomalies_df.iterrows()]
    
    # Generate summary statistics
    severity_counts = anomalies_df['severity'].value_counts().to_dict()
    method_counts = anomalies_df['method'].value_counts().to_dict()
    
    # Calculate financial impact
    total_anomaly_value = anomalies_df['value'].sum()
    avg_anomaly_value = anomalies_df['value'].mean()
    
    return {
        "anomalies": anomalies_list[-50:],  # Limit to last 50 for performance
        "summary": {
            "total_anomalies": len(anomalies_df),
            "severity_breakdown": severity_counts,
            "method_breakdown": method_counts,
            "financial_impact": {
                "total_value": float(total_anomaly_value),
                "average_value": float(avg_anomaly_value),
                "currency": "USD"
            }
        },
        "analysis_period": {
            "start_date": str(hist.index[0]),
            "end_date": str(hist.index[-1]),
            "data_points": len(hist)
        }
    }


@trace_operation("anomaly_detection")
@monitor_performance("anomaly_node")
def node_anomalies(state: AgentState):
    """Detect comprehensive anomalies in treasury operations using multiple methods."""
    from ...infrastructure.observability import get_observability_manager
    
    observability = get_observability_manager()
    logger = observability.get_logger("graph.anomalies")
    entity = state.get("entity")
    
    logger.info("Starting anomaly detection", entity=entity)
    
    try:
        hist = api.get_daily_series(entity)
        
        if len(hist) < 30:
            logger.warning("Insufficient data for anomaly detection", 
                         entity=entity, data_points=len(hist))
            state["result"] = {
                "anomalies": [],
                "summary": "Insufficient historical data for reliable anomaly detection",
                "data_points": len(hist)
            }
            return state
            
        # Use enhanced anomaly detector
        detector = TreasuryAnomalyDetector()
        anomalies_df = detector.detect_cash_flow_anomalies(hist)
        
        # Create result
        state["result"] = _create_anomaly_result(anomalies_df, hist)
        
        logger.info("Anomaly detection completed successfully", 
                   entity=entity, anomalies_found=len(anomalies_df))
        
        observability.record_metric(
            "counter", "anomaly_detections_total", 1,
            {"entity": entity or "all", "status": "success"}
        )
        
        return state
        
    except Exception as e:
        logger.error("Anomaly detection failed", 
                    entity=entity, error=str(e), error_type=type(e).__name__)
        
        observability.record_metric(
            "counter", "anomaly_detections_total", 1,
            {"entity": entity or "all", "status": "failed"}
        )
        
        # Fallback to legacy detection
        try:
            hist = api.get_daily_series(entity)
            legacy_df = outflow_anomalies(hist)
            state["result"] = {
                "anomalies": legacy_df.tail(20).reset_index().rename(
                    columns={"index": "date"}
                ).to_dict(orient="records"),
                "summary": "Used legacy anomaly detection due to system error",
                "error": str(e)
            }
        except Exception as fallback_error:
            state["result"] = {
                "anomalies": [],
                "error": f"Anomaly detection failed: {str(e)}. Fallback failed: {str(fallback_error)}"
            }
        
        return state