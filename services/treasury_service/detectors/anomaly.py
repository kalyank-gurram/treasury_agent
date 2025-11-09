import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
from datetime import datetime, timedelta


class TreasuryAnomalyDetector:
    """Enhanced anomaly detection for treasury operations."""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
    def detect_cash_flow_anomalies(
        self, 
        daily_series: pd.Series, 
        lookback: int = 90, 
        z_threshold: float = 3.0,
        seasonal_adjust: bool = True
    ) -> pd.DataFrame:
        """
        Detect anomalies in daily cash flows using multiple methods.
        
        Args:
            daily_series: Time series of daily cash flows
            lookback: Days to look back for baseline calculation
            z_threshold: Z-score threshold for anomaly detection
            seasonal_adjust: Whether to adjust for seasonal patterns
            
        Returns:
            DataFrame with anomaly details
        """
        if len(daily_series) < lookback:
            lookback = max(30, len(daily_series) // 2)
            
        # Method 1: Statistical anomaly detection (enhanced)
        statistical_anomalies = self._statistical_anomaly_detection(
            daily_series, lookback, z_threshold, seasonal_adjust
        )
        
        # Method 2: Machine learning based detection
        ml_anomalies = self._ml_anomaly_detection(daily_series)
        
        # Method 3: Pattern-based detection
        pattern_anomalies = self._pattern_anomaly_detection(daily_series)
        
        # Combine results
        all_anomalies = []
        
        # Add statistical anomalies
        for idx, row in statistical_anomalies.iterrows():
            all_anomalies.append({
                'date': idx,
                'value': row['value'],
                'method': 'statistical',
                'severity': self._calculate_severity(row['z_score']),
                'z_score': row['z_score'],
                'description': f"Cash flow deviation: {row['z_score']:.2f} std dev from mean"
            })
            
        # Add ML anomalies
        for anomaly in ml_anomalies:
            all_anomalies.append(anomaly)
            
        # Add pattern anomalies
        for anomaly in pattern_anomalies:
            all_anomalies.append(anomaly)
            
        result_df = pd.DataFrame(all_anomalies)
        if len(result_df) > 0:
            result_df = result_df.sort_values(['date', 'severity'], ascending=[True, False])
            result_df = result_df.drop_duplicates(subset=['date'], keep='first')
            
        return result_df
        
    def _statistical_anomaly_detection(
        self, 
        daily_series: pd.Series, 
        lookback: int, 
        z_threshold: float,
        seasonal_adjust: bool
    ) -> pd.DataFrame:
        """Enhanced statistical anomaly detection with seasonal adjustment."""
        series = daily_series.copy()
        
        # Seasonal adjustment using moving averages
        if seasonal_adjust and len(series) >= 30:
            # Weekly seasonal pattern (7-day moving average)
            weekly_trend = series.rolling(window=7, center=True).mean()
            
            # Detrend the series
            series_detrended = series - weekly_trend.fillna(series.mean())
        else:
            series_detrended = series
            
        # Rolling statistics with improved baseline
        rolling_mean = series_detrended.rolling(window=lookback, min_periods=30).mean()
        rolling_std = series_detrended.rolling(window=lookback, min_periods=30).std()
        
        # Calculate z-scores
        z_scores = (series_detrended - rolling_mean) / (rolling_std + 1e-6)
        
        # Detect anomalies (focus on significant outflows and inflows)
        outflow_mask = (series < 0) & (np.abs(z_scores) > z_threshold)
        inflow_mask = (series > 0) & (z_scores > z_threshold)
        anomaly_mask = outflow_mask | inflow_mask
        
        anomalies = pd.DataFrame({
            'value': series[anomaly_mask],
            'z_score': z_scores[anomaly_mask]
        })
        
        return anomalies
        
    def _ml_anomaly_detection(self, daily_series: pd.Series) -> List[Dict]:
        """Machine learning based anomaly detection using Isolation Forest."""
        if len(daily_series) < 50:  # Need sufficient data
            return []
            
        # Feature engineering
        features = self._create_features(daily_series)
        
        if len(features) < 30:  # Need sufficient samples
            return []
            
        # Fit isolation forest
        try:
            features_scaled = self.scaler.fit_transform(features)
            anomaly_labels = self.isolation_forest.fit_predict(features_scaled)
            anomaly_scores = self.isolation_forest.decision_function(features_scaled)
            
            anomalies = []
            for i, (is_anomaly, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
                if is_anomaly == -1:  # Anomaly detected
                    date_idx = features.index[i]
                    anomalies.append({
                        'date': date_idx,
                        'value': daily_series.loc[date_idx],
                        'method': 'ml_isolation_forest',
                        'severity': self._score_to_severity(score),
                        'ml_score': score,
                        'description': f"ML anomaly detected (score: {score:.3f})"
                    })
                    
            return anomalies
            
        except Exception:
            # Fallback if ML fails
            return []
            
    def _pattern_anomaly_detection(self, daily_series: pd.Series) -> List[Dict]:
        """Detect pattern-based anomalies (consecutive unusual days, etc.)."""
        anomalies = []
        
        if len(daily_series) < 14:
            return anomalies
            
        # Detect consecutive large outflows
        large_outflows = daily_series < daily_series.quantile(0.05)  # Bottom 5%
        consecutive_outflows = self._find_consecutive_periods(large_outflows, min_length=3)
        
        for start_date, end_date, length in consecutive_outflows:
            total_outflow = daily_series.loc[start_date:end_date].sum()
            anomalies.append({
                'date': start_date,
                'value': total_outflow,
                'method': 'pattern_consecutive_outflows',
                'severity': 'high' if length >= 5 else 'medium',
                'pattern_length': length,
                'description': f"Consecutive large outflows for {length} days"
            })
            
        # Detect unusual weekend/holiday activity
        weekend_anomalies = self._detect_weekend_anomalies(daily_series)
        anomalies.extend(weekend_anomalies)
        
        return anomalies
        
    def _create_features(self, series: pd.Series) -> pd.DataFrame:
        """Create features for ML-based anomaly detection."""
        features = pd.DataFrame(index=series.index)
        
        # Basic features
        features['value'] = series
        features['abs_value'] = np.abs(series)
        features['is_outflow'] = (series < 0).astype(int)
        
        # Rolling statistics features
        for window in [7, 14, 30]:
            features[f'rolling_mean_{window}'] = series.rolling(window).mean()
            features[f'rolling_std_{window}'] = series.rolling(window).std()
            features[f'rolling_min_{window}'] = series.rolling(window).min()
            features[f'rolling_max_{window}'] = series.rolling(window).max()
            
        # Lag features
        for lag in [1, 7, 30]:
            features[f'lag_{lag}'] = series.shift(lag)
            
        # Day of week features
        features['day_of_week'] = pd.to_datetime(series.index).dayofweek
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Drop rows with NaN values
        features = features.dropna()
        
        return features
        
    def _find_consecutive_periods(
        self, 
        boolean_series: pd.Series, 
        min_length: int = 2
    ) -> List[Tuple]:
        """Find consecutive True periods in a boolean series."""
        periods = []
        start_date = None
        length = 0
        
        for date, value in boolean_series.items():
            if value and start_date is None:
                start_date = date
                length = 1
            elif value and start_date is not None:
                length += 1
            elif not value and start_date is not None:
                if length >= min_length:
                    end_date = boolean_series.index[boolean_series.index.get_loc(date) - 1]
                    periods.append((start_date, end_date, length))
                start_date = None
                length = 0
                
        # Handle case where series ends with True values
        if start_date is not None and length >= min_length:
            end_date = boolean_series.index[-1]
            periods.append((start_date, end_date, length))
            
        return periods
        
    def _detect_weekend_anomalies(self, series: pd.Series) -> List[Dict]:
        """Detect unusual activity on weekends."""
        anomalies = []
        
        # Convert index to datetime if it's not already
        if not isinstance(series.index, pd.DatetimeIndex):
            try:
                series.index = pd.to_datetime(series.index)
            except (ValueError, TypeError):
                return anomalies
                
        # Find weekend transactions that are unusually large
        weekend_mask = series.index.dayofweek.isin([5, 6])  # Saturday, Sunday
        weekend_series = series[weekend_mask]
        
        if len(weekend_series) == 0:
            return anomalies
            
        # Compare weekend activity to weekday baseline
        weekday_series = series[~weekend_mask]
        if len(weekday_series) > 0:
            weekday_threshold = np.percentile(np.abs(weekday_series), 90)
            
            for date, value in weekend_series.items():
                if np.abs(value) > weekday_threshold:
                    anomalies.append({
                        'date': date,
                        'value': value,
                        'method': 'pattern_weekend_activity',
                        'severity': 'medium',
                        'description': f"Unusual weekend activity: ${value:,.2f}"
                    })
                    
        return anomalies
        
    def _calculate_severity(self, z_score: float) -> str:
        """Calculate severity based on z-score."""
        abs_z = abs(z_score)
        if abs_z >= 4:
            return 'critical'
        elif abs_z >= 3:
            return 'high'
        elif abs_z >= 2:
            return 'medium'
        else:
            return 'low'
            
    def _score_to_severity(self, ml_score: float) -> str:
        """Convert ML anomaly score to severity level."""
        if ml_score <= -0.3:
            return 'critical'
        elif ml_score <= -0.2:
            return 'high'
        elif ml_score <= -0.1:
            return 'medium'
        else:
            return 'low'


# Legacy function for backward compatibility
def outflow_anomalies(daily_series: pd.Series, lookback: int = 90, z: float = 3.0):
    """Legacy function - use TreasuryAnomalyDetector for new implementations."""
    detector = TreasuryAnomalyDetector()
    anomalies = detector.detect_cash_flow_anomalies(daily_series, lookback, z)
    
    # Convert to legacy format
    legacy_format = pd.DataFrame({
        "value": anomalies['value'] if len(anomalies) > 0 else [],
        "z": anomalies.get('z_score', []) if len(anomalies) > 0 else []
    })
    
    if len(anomalies) > 0:
        legacy_format.index = anomalies['date']
        
    return legacy_format