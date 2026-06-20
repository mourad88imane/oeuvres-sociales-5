"""
============================================================
APPROVAL MATRIX SERVICE — Vérification des règles d'approbation
============================================================
Utilisé par les workflows métier (prêts, couverture médicale)
pour déterminer si une demande doit être escaladée en
fonction du montant et de la configuration.
"""

from decimal import Decimal
from typing import Optional


def get_approval_matrix_for_amount(module: str, amount: Decimal):
    """
    Cherche la règle de matrice d'approbation correspondant
    au montant pour un module donné.

    Retourne le niveau d'approbation le plus élevé si plusieurs
    règles matchent, ou None si aucune règle ne s'applique.
    """
    from django.apps import apps
    ApprovalMatrix = apps.get_model("administration", "ApprovalMatrix")
    rules = ApprovalMatrix.objects.filter(
        module=module,
        is_active=True,
    )

    # Filtrer les règles où le montant est dans l'intervalle
    matching = []
    for rule in rules:
        min_ok = rule.min_amount is None or amount >= rule.min_amount
        max_ok = rule.max_amount is None or amount <= rule.max_amount
        if min_ok and max_ok:
            matching.append(rule)

    if not matching:
        return None

    # Retourner celle avec le niveau d'approbation le plus élevé
    return max(matching, key=lambda r: r.approval_level)


def requires_director_approval(module: str, amount: Decimal) -> bool:
    """
    Vérifie si le montant dépasse le seuil nécessitant
    une approbation du directeur.
    """
    matrix = get_approval_matrix_for_amount(module, amount)
    if not matrix:
        return False
    # Niveau 2+ = escalation requise (1 = manager, 2 = director, 3 = committee)
    return matrix.approval_level >= 2


def get_required_roles_for_amount(module: str, amount: Decimal):
    """
    Retourne les rôles requis pour approuver un montant donné.
    """
    matrix = get_approval_matrix_for_amount(module, amount)
    if not matrix:
        return []
    return list(matrix.required_roles.all())


def get_escalation_threshold(module: str) -> Optional[Decimal]:
    """
    Retourne le montant minimum (le plus bas) qui déclenche
    une escalation, ou None si pas de règle active.
    """
    from django.apps import apps
    ApprovalMatrix = apps.get_model("administration", "ApprovalMatrix")
    first = ApprovalMatrix.objects.filter(
        module=module, is_active=True,
        approval_level__gte=2,
    ).order_by("min_amount").first()
    if first and first.min_amount is not None:
        return first.min_amount
    return None
