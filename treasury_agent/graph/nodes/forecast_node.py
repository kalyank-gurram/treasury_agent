"""Forecasting node for Treasury Agent."""

from treasury_agent.forecasting.arima_forecaster import arima_forecast
from treasury_agent.forecasting.gbr_forecaster import gbr_forecast
from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_forecast(state: AgentState):
    """Generate cash flow forecasts using ARIMA and Gradient Boost ensemble."""
    hist = api.get_daily_series(state.get("entity"))
    ar = arima_forecast(hist, 30)
    gb = gbr_forecast(hist, 30)
    fc = (ar + gb) / 2
    state["result"] = {"history_tail": hist.tail(30).to_dict(), "forecast": fc.to_dict()}
    return state