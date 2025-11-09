"""Enhanced ARIMA forecaster plugin with advanced features."""

from typing import List, Dict, Any
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose

from .plugins.base import ForecasterPlugin, PluginMetadata, PluginType


class EnhancedArimaForecaster(ForecasterPlugin):
    """Enhanced ARIMA forecaster with seasonal decomposition."""
    
    def __init__(self):
        self._model_cache = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="enhanced_arima_forecaster",
            version="1.0.0",
            description="ARIMA forecaster with seasonal decomposition and model caching",
            plugin_type=PluginType.FORECASTER,
            author="Treasury Agent Team",
            dependencies=["statsmodels", "pandas"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the forecaster."""
        self.order = config.get("arima_order", (2, 1, 2))
        self.seasonal_order = config.get("seasonal_order", (1, 1, 1, 12))
        self.use_seasonal = config.get("use_seasonal", True)
        self.cache_models = config.get("cache_models", True)
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._model_cache.clear()
    
    async def forecast(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int
    ) -> List[Dict[str, Any]]:
        """Generate enhanced ARIMA forecast."""
        try:
            # Convert to pandas Series
            df = pd.DataFrame(historical_data)
            if 'date' in df.columns and 'amount' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                series = df['amount'].asfreq('D').fillna(0)
            else:
                # Fallback: assume daily data
                series = pd.Series([item.get('amount', 0) for item in historical_data])
                series.index = pd.date_range(
                    start=pd.Timestamp.today() - pd.Timedelta(days=len(series)-1),
                    periods=len(series),
                    freq='D'
                )
            
            # Check cache
            series_hash = hash(tuple(series.values))
            if self.cache_models and series_hash in self._model_cache:
                model_result = self._model_cache[series_hash]
            else:
                # Seasonal decomposition if enabled
                if self.use_seasonal and len(series) >= 24:  # Need enough data
                    decomposition = seasonal_decompose(series, model='additive', period=12)
                    deseasonalized = series - decomposition.seasonal
                    
                    # Fit ARIMA on deseasonalized data
                    model = ARIMA(deseasonalized, order=self.order)
                    model_result = model.fit()
                else:
                    # Standard ARIMA
                    model = ARIMA(series, order=self.order)
                    model_result = model_result = model.fit()
                
                # Cache the model
                if self.cache_models:
                    self._model_cache[series_hash] = model_result
            
            # Generate forecast
            forecast = model_result.forecast(steps=forecast_days)
            
            # Create forecast output
            forecast_dates = pd.date_range(
                start=series.index.max() + pd.Timedelta(days=1),
                periods=forecast_days,
                freq='D'
            )
            
            result = []
            for i, (date, value) in enumerate(zip(forecast_dates, forecast)):
                result.append({
                    'date': date.isoformat(),
                    'forecast_value': float(value),
                    'forecast_type': 'enhanced_arima',
                    'confidence_interval_lower': float(value * 0.9),  # Simplified CI
                    'confidence_interval_upper': float(value * 1.1),
                    'day_ahead': i + 1
                })
            
            return result
            
        except Exception as e:
            # Fallback to simple mean forecast
            mean_value = sum(item.get('amount', 0) for item in historical_data[-30:]) / 30
            result = []
            for i in range(forecast_days):
                result.append({
                    'date': (pd.Timestamp.today() + pd.Timedelta(days=i+1)).isoformat(),
                    'forecast_value': mean_value,
                    'forecast_type': 'fallback_mean',
                    'confidence_interval_lower': mean_value * 0.8,
                    'confidence_interval_upper': mean_value * 1.2,
                    'day_ahead': i + 1,
                    'error': str(e)
                })
            return result