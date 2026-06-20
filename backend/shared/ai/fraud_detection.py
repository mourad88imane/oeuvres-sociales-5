"""
============================================================
FRAUD DETECTION — Détection de fraudes et d'anomalies
============================================================
Méthodes :
  - Règles heuristiques (doublons, seuils, fréquences)
  - Z-score sur les montants
  - Détection de cumul (même bénéficiaire, période courte)
  - Alerte sur nouveaux ayants droit
"""

import logging
from collections import Counter
from datetime import timedelta
from statistics import mean, stdev

from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.translation import gettext as _

logger = logging.getLogger("shared.ai.fraud_detection")

FRAUD_RULES = [
    "duplicate_payment",
    "unusual_amount",
    "high_frequency",
    "threshold_proximity",
    "new_beneficiary_claim",
    "amount_rounding",
]


class FraudDetector:

    def detect_all(self, days: int = 90, save: bool = True) -> dict:
        """Run all fraud detection rules and return findings."""
        all_flags = []
        all_flags.extend(self._detect_duplicate_payments(days))
        all_flags.extend(self._detect_unusual_amounts(days))
        all_flags.extend(self._detect_high_frequency(days))
        all_flags.extend(self._detect_threshold_proximity(days))
        all_flags.extend(self._detect_new_beneficiary_claims(days))
        all_flags.extend(self._detect_amount_rounding(days))

        if save:
            self._save_flags(all_flags)

        severity_counts = Counter(f["severity"] for f in all_flags)
        return {
            "period_days": days,
            "total_flags": len(all_flags),
            "severity_breakdown": dict(severity_counts),
            "rules_triggered": list(set(f["rule"] for f in all_flags)),
            "flags": sorted(all_flags, key=lambda x: x["severity"], reverse=True),
        }

    def _get_recent_payments(self, days: int):
        from django.apps import apps
        try:
            Payment = apps.get_model("finance", "Payment")
        except LookupError:
            return []
        cutoff = timezone.now() - timedelta(days=days)
        return list(
            Payment.objects.filter(
                executed_date__gte=cutoff,
                status="paid",
                is_deleted=False,
            ).select_related("benefit", "benefit__employee")
        )

    def _get_recent_benefits(self, days: int):
        from django.apps import apps
        try:
            Benefit = apps.get_model("benefits", "Benefit")
        except LookupError:
            return []
        cutoff = timezone.now() - timedelta(days=days)
        return list(
            Benefit.objects.alive().filter(created_at__gte=cutoff)
        )

    def _detect_duplicate_payments(self, days: int) -> list[dict]:
        """Find payments with same amount + same benefit within short period."""
        payments = self._get_recent_payments(days)
        flags = []
        seen = {}
        for p in payments:
            key = (p.amount, p.benefit_id)
            if key in seen:
                prev = seen[key]
                if p.executed_date and prev.executed_date:
                    diff_days = abs((p.executed_date - prev.executed_date).days)
                    if diff_days <= 3:
                        flags.append({
                            "rule": "duplicate_payment",
                            "severity": "high" if diff_days == 0 else "medium",
                            "title": _("Paiement en double détecté"),
                            "detail": _(
                                f"Paiement {p.id} : {p.amount} DA (x2) à {diff_days}j d'intervalle"
                            ),
                            "target_type": "Payment",
                            "target_id": str(p.id),
                            "related_id": str(prev.id),
                            "value": float(p.amount),
                            "expected": float(prev.amount),
                        })
            else:
                seen[key] = p
        return flags

    def _detect_unusual_amounts(self, days: int) -> list[dict]:
        """Z-score based amount outlier detection."""
        payments = self._get_recent_payments(days)
        if len(payments) < 5:
            return []
        amounts = [float(p.amount) for p in payments if p.amount]
        if not amounts:
            return []
        m = mean(amounts)
        s = stdev(amounts) if len(amounts) > 1 else 1
        flags = []
        for p in payments:
            z = (float(p.amount) - m) / s if s else 0
            if abs(z) > 2.5:
                flags.append({
                    "rule": "unusual_amount",
                    "severity": "critical" if abs(z) > 4 else "high",
                    "title": _("Montant anormal détecté"),
                    "detail": _(
                        f"Paiement {p.id} : {p.amount} DA (z-score={z:.1f}, "
                        f"moyenne={m:.0f}, écart-type={s:.0f})"
                    ),
                    "target_type": "Payment",
                    "target_id": str(p.id),
                    "value": float(p.amount),
                    "expected": round(m, 2),
                    "zscore": round(z, 2),
                })
        return flags

    def _detect_high_frequency(self, days: int) -> list[dict]:
        """Detect unusual number of payments per employee."""
        payments = self._get_recent_payments(days)
        if not payments:
            return []
        emp_counts = Counter()
        for p in payments:
            emp = p.benefit.employee_id if p.benefit else None
            if emp:
                emp_counts[emp] += 1
        if not emp_counts:
            return []
        counts = list(emp_counts.values())
        m = mean(counts)
        s = stdev(counts) if len(counts) > 1 else 1
        flags = []
        for emp_id, count in emp_counts.items():
            z = (count - m) / s if s else 0
            if count > 3 and z > 2:
                flags.append({
                    "rule": "high_frequency",
                    "severity": "medium" if z < 3 else "high",
                    "title": _("Fréquence élevée de paiements"),
                    "detail": _(
                        f"Employé {emp_id} : {count} paiements en {days}j "
                        f"(moyenne={m:.1f}, z-score={z:.1f})"
                    ),
                    "target_type": "Employee",
                    "target_id": str(emp_id),
                    "value": float(count),
                    "expected": round(m, 1),
                })
        return flags

    def _detect_threshold_proximity(self, days: int) -> list[dict]:
        """Detect amounts just below common thresholds (e.g. 100000, 50000)."""
        payments = self._get_recent_payments(days)
        flags = []
        thresholds = [50000, 100000, 200000, 500000, 1000000]
        for p in payments:
            amt = float(p.amount)
            for t in thresholds:
                if t * 0.95 <= amt < t and amt > 0:
                    flags.append({
                        "rule": "threshold_proximity",
                        "severity": "medium",
                        "title": _("Montant proche d'un seuil"),
                        "detail": _(
                            f"Paiement {p.id} : {amt:.0f} DA (seuil {t} DA, "
                            f"écart {t - amt:.0f} DA)"
                        ),
                        "target_type": "Payment",
                        "target_id": str(p.id),
                        "value": amt,
                        "expected": float(t),
                    })
                    break
        return flags

    def _detect_new_beneficiary_claims(self, days: int) -> list[dict]:
        """Flag benefits claimed by recently added beneficiaries."""
        try:
            from django.apps import apps
            Beneficiary = apps.get_model("beneficiaries", "Beneficiary")
        except LookupError:
            return []
        cutoff = timezone.now() - timedelta(days=30)
        new_bens = Beneficiary.objects.alive().filter(created_at__gte=cutoff)
        flags = []
        new_ben_map = {}
        for b in new_bens:
            employee_id = str(b.employee_id) if b.employee_id else None
            relation = b.relationship if hasattr(b, "relationship") else ""
            new_ben_map[str(b.id)] = {
                "name": str(b),
                "employee_id": employee_id,
                "relation": relation,
            }

        benefits = self._get_recent_benefits(days)
        for b in benefits:
            if hasattr(b, "employee_id") and b.employee_id:
                emp_id = str(b.employee_id)
            else:
                continue
            ben_id = str(b.id)
            for nb_id, nb_info in new_ben_map.items():
                if nb_info["employee_id"] == emp_id:
                    flags.append({
                        "rule": "new_beneficiary_claim",
                        "severity": "medium",
                        "title": _("Ayant droit récent avec demande"),
                        "detail": _(
                            f"Ayant droit « {nb_info['name']} » "
                            f"(< 30j, {nb_info['relation']}) lié à la prestation {ben_id}"
                        ),
                        "target_type": "Benefit",
                        "target_id": ben_id,
                        "value": 1.0,
                        "expected": 0.0,
                    })
        return flags

    def _detect_amount_rounding(self, days: int) -> list[dict]:
        """Detect suspiciously round amounts (potential manipulation)."""
        payments = self._get_recent_payments(days)
        flags = []
        for p in payments:
            amt = float(p.amount)
            if amt > 0 and amt % 10000 == 0 and amt >= 100000:
                flags.append({
                    "rule": "amount_rounding",
                    "severity": "low",
                    "title": _("Montant suspectement rond"),
                    "detail": _(
                        f"Paiement {p.id} : {amt:.0f} DA (multiple de 10 000)"
                    ),
                    "target_type": "Payment",
                    "target_id": str(p.id),
                    "value": amt,
                    "expected": None,
                })
        return flags

    def _save_flags(self, flags: list[dict]):
        from .models import AIAnomaly, AIModelRegistry

        model, _ = AIModelRegistry.objects.get_or_create(
            name="fraud_detector_v1",
            defaults={
                "version": "1.0.0",
                "task_type": "anomaly",
                "status": "production",
            },
        )
        for f in flags:
            try:
                AIAnomaly.objects.create(
                    model=model,
                    detection_method=f"fraud_{f['rule']}",
                    severity=f["severity"],
                    target_type=f["target_type"],
                    target_id=f["target_id"],
                    metric_name=f["title"],
                    expected_value=f.get("expected"),
                    actual_value=f.get("value"),
                    explanation=f.get("detail", ""),
                )
            except Exception as exc:
                logger.warning("Failed to save fraud flag: %s", exc)


fraud_detector = FraudDetector()
