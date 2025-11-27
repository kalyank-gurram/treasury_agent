"""
Narrative generation utilities for Treasury Agent CFO briefing.
"""

from datetime import datetime


def daily_cfo_brief(metrics: dict) -> str:
    """
    Generate an executive-friendly CFO briefing narrative based on
    balances, anomalies, and counterparty exposure metrics.

    Args:
        metrics (dict): Dictionary containing:
            - balances (dict): {entity: balance}
            - anomalies (dict): recent anomaly signals
            - top_counterparties (list): list of exposure records

    Returns:
        str: Human-readable CFO briefing summary.
    """

    balances = metrics.get("balances", {})
    anomalies = metrics.get("anomalies", {})
    exposure = metrics.get("top_counterparties", [])

    date_str = datetime.now().strftime("%B %d, %Y")

    # ---- Build balance summary ----
    balance_lines = []
    for entity, bal in balances.items():
        balance_lines.append(f"- {entity}: ${bal:,.2f}")

    balance_section = (
        "No balance data available."
        if not balance_lines
        else "\n".join(balance_lines)
    )

    # ---- Build anomaly summary ----
    anomaly_section = (
        "No unusual cash outflows detected in recent trend."
        if not anomalies
        else f"Recent anomaly indicators (last 5 days): {anomalies}"
    )

    # ---- Build counterparty exposure ----
    if exposure:
        cp_lines = []
        for cp in exposure:
            name = cp.get("counterparty") or cp.get("name") or "Unknown"
            amount = cp.get("exposure") or cp.get("amount") or 0
            cp_lines.append(f"- {name}: ${amount:,.2f}")
        exposure_section = "\n".join(cp_lines)
    else:
        exposure_section = "No significant counterparty exposures recorded."

    # ---- Final narrative ----
    narrative = f"""
📊 **Daily CFO Treasury Brief — {date_str}**

**1. Cash & Liquidity Balances**
{balance_section}

**2. Cashflow Anomalies**
{anomaly_section}

**3. Top Counterparty Exposures**
{exposure_section}

---
Generated automatically by the Treasury Agent analytics engine.
"""
    return narrative.strip()
