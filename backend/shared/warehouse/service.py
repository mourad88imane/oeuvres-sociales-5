"""
Data Warehouse preparation module.

Provides the foundation for future BI capabilities:
- Materialized view management
- ETL pipeline stubs
- Aggregation tables (summary tables for reporting)
- Star-schema dimension stubs

In production, these should use PostgreSQL materialized views
and/or dedicated summary tables refreshed by Celery tasks.
"""

import logging

from django.db import connection

logger = logging.getLogger("shared.warehouse")


class WarehouseService:
    """
    Service for managing data warehouse objects.

    Phase 1: Materialized view management (PostgreSQL)
    Phase 2: Dimensional model (star schema)
    Phase 3: ETL pipelines for external BI tools (Metabase, PowerBI, etc.)
    """

    # ── Materialized views ────────────────────────────────

    MV_MONTHLY_AGG = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS dw_monthly_agg AS
    SELECT
        DATE_TRUNC('month', be.created_at) AS month,
        COUNT(DISTINCT be.id) AS benefits_count,
        COALESCE(SUM(be.amount), 0) AS benefits_amount,
        COUNT(DISTINCT emp.id) AS employees_with_benefits,
        COUNT(DISTINCT CASE WHEN be.status = 'paid' THEN be.id END) AS paid_count,
        COALESCE(SUM(CASE WHEN be.status = 'paid' THEN be.amount ELSE 0 END), 0) AS paid_amount
    FROM benefits_benefit be
    JOIN employees_employee emp ON be.employee_id = emp.id
    WHERE be.is_deleted = FALSE
    GROUP BY DATE_TRUNC('month', be.created_at)
    ORDER BY 1 DESC;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_dw_monthly_agg_month
    ON dw_monthly_agg (month);
    """

    MV_BUDGET_CONS = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS dw_budget_consumption AS
    SELECT
        bg.fiscal_year_id,
        bg.id AS budget_id,
        bg.code AS budget_code,
        bg.amount AS budget_amount,
        COALESCE(SUM(py.amount), 0) AS paid_amount,
        CASE WHEN bg.amount > 0
            THEN ROUND((COALESCE(SUM(py.amount), 0) / bg.amount) * 100, 1)
            ELSE 0
        END AS consumption_pct
    FROM finance_budget bg
    LEFT JOIN finance_payment py ON py.budget_id = bg.id AND py.status = 'paid' AND py.is_deleted = FALSE
    WHERE bg.is_deleted = FALSE
    GROUP BY bg.id, bg.fiscal_year_id, bg.code, bg.amount;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_dw_budget_cons_budget
    ON dw_budget_consumption (budget_id);
    """

    MV_EMPLOYEE_TURNOVER = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS dw_employee_turnover AS
    SELECT
        DATE_TRUNC('month', COALESCE(emp.hire_date, emp.created_at)) AS hire_month,
        COUNT(*) AS hired,
        COUNT(CASE WHEN emp.status = 'inactive' THEN 1 END) AS departed
    FROM employees_employee emp
    WHERE emp.is_deleted = FALSE
    GROUP BY DATE_TRUNC('month', COALESCE(emp.hire_date, emp.created_at))
    ORDER BY 1 DESC;
    """

    def refresh_all_views(self):
        """Refresh all materialized views concurrently (non-blocking)."""
        views = ["dw_monthly_agg", "dw_budget_consumption", "dw_employee_turnover"]
        refreshed = []
        with connection.cursor() as cursor:
            for view in views:
                try:
                    cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                    refreshed.append(view)
                except Exception as exc:
                    logger.warning("Could not refresh MV %s: %s", view, exc)
        logger.info("Refreshed materialized views: %s", refreshed)
        return refreshed

    def ensure_views(self):
        """Create materialized views if they don't exist."""
        with connection.cursor() as cursor:
            for sql in [self.MV_MONTHLY_AGG, self.MV_BUDGET_CONS, self.MV_EMPLOYEE_TURNOVER]:
                try:
                    cursor.execute(sql)
                except Exception as exc:
                    logger.warning("Could not create MV: %s", exc)

    # ── Star schema dimension stubs ─────────────────────────

    DIMENSION_MODELS = [
        "employees.Employee",
        "employees.Department",
        "benefits.BenefitType",
        "conventions.Partner",
        "finance.FiscalYear",
        "finance.Budget",
    ]

    FACT_TABLES = [
        "benefits.Benefit",  # Fact: benefit requests
        "finance.Payment",  # Fact: payments
        "conventions.Convention",  # Fact: conventions
        "reporting.KpiSnapshot",  # Fact: KPI measurements
    ]

    def get_schema_report(self):
        """Return a report of the current data model for BI tool configuration."""
        return {
            "dimensions": self.DIMENSION_MODELS,
            "facts": self.FACT_TABLES,
            "materialized_views": [
                "dw_monthly_agg (monthly benefits aggregation)",
                "dw_budget_consumption (budget vs actuals)",
                "dw_employee_turnover (hires and departures)",
            ],
            "time_dimensions": {
                "date": "Primary date dimension",
                "month": "Aggregated month level",
                "year": "Aggregated year level",
            },
        }

    # ── ETL pipeline stubs ─────────────────────────────────

    def extract_full(self):
        """
        Stub: full data extraction for ETL.
        In production: export all fact/dimension tables to staging area.
        """
        logger.info("ETL extract_full: stub — no-op")
        return {"status": "stub", "tables": self.FACT_TABLES + self.DIMENSION_MODELS}

    def transform_and_load(self, data):
        """
        Stub: transform and load into warehouse schema.
        In production: apply business rules, clean data, load to star schema.
        """
        logger.info("ETL transform_and_load: stub — no-op")
        return {"status": "stub", "rows_processed": 0}
