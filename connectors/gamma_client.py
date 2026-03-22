from datetime import datetime
from typing import Any
import requests

from models.enums import Asset, Horizon
from models.market import Market


class GammaClient:
    """Minimal market discovery client for Polymarket Gamma API."""

    def __init__(self, base_url: str = "https://gamma-api.polymarket.com"):
        self.base_url = base_url.rstrip("/")

    def discover_markets(self) -> list[Market]:
        url = f"{self.base_url}/markets"
        params = {"active": "true", "closed": "false", "limit": 500}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        markets: list[Market] = []
        for item in payload:
            parsed = self._parse_market(item)
            if parsed:
                markets.append(parsed)
        return markets

    def _parse_market(self, item: dict[str, Any]) -> Market | None:
        question = (item.get("question") or "").upper()
        asset = None
        for symbol in ("BTC", "ETH", "SOL"):
            if symbol in question:
                asset = Asset(symbol)
                break
        if asset is None:
            return None

        horizon = Horizon.M5 if "5 MIN" in question or "5M" in question else None
        if horizon is None and ("15 MIN" in question or "15M" in question):
            horizon = Horizon.M15
        if horizon is None:
            return None

        outcomes = item.get("outcomes") or []
        yes_token = next((o.get("token_id") for o in outcomes if (o.get("name") or "").upper() == "YES"), None)
        no_token = next((o.get("token_id") for o in outcomes if (o.get("name") or "").upper() == "NO"), None)
        if not yes_token or not no_token:
            return None

        end_iso = item.get("endDate") or item.get("end_date_iso")
        if not end_iso:
            return None
        end_time = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))

        return Market(
            market_id=str(item["id"]),
            asset=asset,
            horizon=horizon,
            yes_token_id=str(yes_token),
            no_token_id=str(no_token),
            end_time=end_time,
            is_active=bool(item.get("active", True)),
        )
