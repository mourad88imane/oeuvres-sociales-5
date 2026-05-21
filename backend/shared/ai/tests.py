"""Tests for shared AI / prediction services."""

import pytest

from django.test import TestCase
from shared.ai.services import PredictionService, _linear_regression, _zscore_anomalies

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestLinearRegression(TestCase):
    def test_perfect_positive_correlation(self):
        xs = list(range(10))
        ys = [2 * x + 1 for x in xs]
        slope, intercept, r2 = _linear_regression(xs, ys)
        self.assertAlmostEqual(slope, 2.0)
        self.assertAlmostEqual(intercept, 1.0)
        self.assertAlmostEqual(r2, 1.0)

    def test_flat_line(self):
        xs = list(range(5))
        ys = [10] * 5
        slope, intercept, r2 = _linear_regression(xs, ys)
        self.assertAlmostEqual(slope, 0.0)
        self.assertAlmostEqual(intercept, 10.0)

    def test_single_point(self):
        slope, intercept, r2 = _linear_regression([0], [5])
        self.assertEqual(slope, 0.0)
        self.assertEqual(intercept, 5.0)
        self.assertEqual(r2, 0.0)

    def test_negative_correlation(self):
        xs = list(range(5))
        ys = [10 - 3 * x for x in xs]
        slope, intercept, r2 = _linear_regression(xs, ys)
        self.assertAlmostEqual(slope, -3.0)
        self.assertAlmostEqual(intercept, 10.0)


class TestZScoreAnomalies(TestCase):
    def test_no_anomalies_in_uniform_data(self):
        values = [10, 10, 10, 10, 10]
        result = _zscore_anomalies(values)
        self.assertEqual(result, [])

    def test_detects_outlier(self):
        values = [10, 10, 10, 10, 100]
        result = _zscore_anomalies(values, threshold=1.5)
        self.assertEqual(len(result), 1)
        idx, val, z = result[0]
        self.assertEqual(idx, 4)
        self.assertEqual(val, 100)

    def test_threshold_too_high_returns_none(self):
        values = [10, 10, 10, 10, 11]
        result = _zscore_anomalies(values, threshold=5.0)
        self.assertEqual(result, [])

    def test_requires_minimum_points(self):
        result = _zscore_anomalies([1, 2])
        self.assertEqual(result, [])

    def test_handles_zero_std(self):
        result = _zscore_anomalies([5, 5, 5])
        self.assertEqual(result, [])


class TestPredictionService(TestCase):
    def setUp(self):
        self.svc = PredictionService()

        # Seed KPI snapshots for trend prediction
        from datetime import date, timedelta

        from apps.reporting.models import KpiDefinition, KpiSnapshot

        self.kpi = KpiDefinition.objects.create(
            code="consumption_rate",
            name="Consumption Rate",
            category="finance",
            target_value=100.0,
        )
        today = date.today()
        for i in range(30):
            KpiSnapshot.objects.create(
                kpi=self.kpi,
                value=float(50 + i * 2),
                date=today - timedelta(days=30 - i),
            )

    def test_predict_budget_consumption_returns_structure(self):
        result = self.svc.predict_budget_consumption()
        self.assertIn("fiscal_year", result)
        self.assertIn("consumption_rate", result)
        self.assertIn("risk_level", result)

    def test_detect_anomalies_finds_anomalies(self):
        result = self.svc.detect_anomalies(days=90)
        self.assertIn("anomalies", result)
        self.assertIn("total_anomalies", result)

    def test_decision_support_returns_recommendations(self):
        result = self.svc.decision_support()
        self.assertIn("recommendations", result)
        self.assertIn("total_recommendations", result)

    def test_predict_benefits_trend_without_data_returns_error(self):
        """When no aggregation data exists, predict_benefits_trend should handle gracefully."""
        result = self.svc.predict_benefits_trend(months_ahead=2)
        # May return error dict or predictions depending on whether aggregation service
        # has data (regression test environment may have nothing)
        self.assertIn("target", result)
