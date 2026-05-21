"""Reporting engine — base aggregation service."""

import logging
from typing import Any

logger = logging.getLogger("shared.reporting")


class BaseAggregationService:
    """
    Abstract aggregation service for reporting.

    Subclasses must implement the data-fetching methods for their project.
    """

    def get_global_stats(self, user=None) -> dict[str, Any]:
        raise NotImplementedError

    def get_monthly_trends(self, months: int = 12) -> list[dict]:
        raise NotImplementedError

    def get_top_stats(self, category: str = "", limit: int = 5) -> list[dict]:
        raise NotImplementedError

    def get_all_kpis(self) -> list[dict]:
        raise NotImplementedError

    def compute_and_snapshot_kpis(self) -> list[dict]:
        raise NotImplementedError

    def get_report_data(self, report, filters: dict | None = None) -> list[dict]:
        """Fetch data for a given report definition."""
        raise NotImplementedError
