"""
Seed migration: populate WorkflowState, WorkflowTransition, WorkflowTransitionRole
from the 4 hardcoded workflow definitions (loans, benefits, medical coverage).
"""
from django.db import migrations


WORKFLOWS = {
    ("loans", "Loan"): {
        "states": [
            ("draft", "Brouillon", "مسودة", "#6B7280", True, False, 0),
            ("submitted", "Soumise", "مقدمة", "#3B82F6", False, False, 1),
            ("under_review", "En instruction", "قيد الدراسة", "#8B5CF6", False, False, 2),
            ("on_hold", "En attente", "معلقة", "#F59E0B", False, False, 3),
            ("pending_director_approval", "En attente du directeur", "في انتظار المدير", "#EC4899", False, False, 4),
            ("validated", "Validée", "مصادق عليها", "#10B981", False, False, 5),
            ("paid", "Payée", "مدفوعة", "#059669", False, True, 6),
            ("rejected", "Rejetée", "مرفوضة", "#EF4444", False, True, 7),
            ("cancelled", "Annulée", "ملغاة", "#9CA3AF", False, True, 8),
        ],
        "transitions": [
            ("draft", "submitted", "Soumettre", "تقديم", ["admin", "gestionnaire"], False, False, "LOW", 0),
            ("submitted", "under_review", "Prendre en charge", "تولي المعالجة", ["admin", "gestionnaire"], False, False, "LOW", 1),
            ("submitted", "on_hold", "Mettre en attente", "تعليق", ["admin", "gestionnaire"], True, False, "MEDIUM", 2),
            ("submitted", "pending_director_approval", "Escalader au directeur", "رفع للمدير", ["admin", "gestionnaire"], True, False, "HIGH", 3),
            ("under_review", "on_hold", "Mettre en attente", "تعليق", ["admin", "gestionnaire"], True, False, "MEDIUM", 4),
            ("on_hold", "submitted", "Re-soumettre", "إعادة تقديم", ["admin", "gestionnaire"], False, False, "LOW", 5),
            ("under_review", "validated", "Valider", "مصادقة", ["admin", "gestionnaire"], False, False, "HIGH", 6),
            ("submitted", "validated", "Valider directement", "مصادقة مباشرة", ["admin"], False, False, "HIGH", 7),
            ("pending_director_approval", "validated", "Approuver (Directeur)", "موافقة المدير", ["admin", "director"], False, False, "HIGH", 8),
            ("pending_director_approval", "rejected", "Rejeter (Directeur)", "رفض المدير", ["admin", "director"], True, True, "CRITICAL", 9),
            ("validated", "paid", "Confirmer le paiement", "تأكيد الدفع", ["admin", "comptable"], False, False, "CRITICAL", 10),
            ("submitted", "rejected", "Rejeter", "رفض", ["admin", "gestionnaire"], True, True, "HIGH", 11),
            ("under_review", "rejected", "Rejeter", "رفض", ["admin", "gestionnaire"], True, True, "HIGH", 12),
            ("validated", "rejected", "Rejeter après validation", "رفض بعد المصادقة", ["admin", "comptable"], True, True, "CRITICAL", 13),
            ("draft", "cancelled", "Annuler", "إلغاء", ["admin", "gestionnaire"], False, True, "LOW", 14),
            ("submitted", "cancelled", "Annuler", "إلغاء", ["admin", "gestionnaire"], True, True, "MEDIUM", 15),
            ("on_hold", "cancelled", "Annuler", "إلغاء", ["admin", "gestionnaire"], True, True, "MEDIUM", 16),
            ("pending_director_approval", "cancelled", "Annuler", "إلغاء", ["admin"], True, True, "MEDIUM", 17),
        ],
    },
    ("benefits", "Benefit"): {
        "states": [
            ("draft", "Brouillon", "مسودة", "#6B7280", True, False, 0),
            ("submitted", "Soumise", "مقدمة", "#3B82F6", False, False, 1),
            ("under_review", "En instruction", "قيد الدراسة", "#8B5CF6", False, False, 2),
            ("on_hold", "En attente", "معلقة", "#F59E0B", False, False, 3),
            ("validated", "Validée", "مصادق عليها", "#10B981", False, False, 4),
            ("paid", "Payée", "مدفوعة", "#059669", False, True, 5),
            ("rejected", "Rejetée", "مرفوضة", "#EF4444", False, True, 6),
            ("cancelled", "Annulée", "ملغاة", "#9CA3AF", False, True, 7),
        ],
        "transitions": [
            ("draft", "submitted", "Soumettre", "تقديم", ["admin", "gestionnaire"], False, False, "LOW", 0),
            ("submitted", "under_review", "Prendre en charge", "تولي المعالجة", ["admin", "gestionnaire"], False, False, "LOW", 1),
            ("submitted", "on_hold", "Mettre en attente", "تعليق", ["admin", "gestionnaire"], True, False, "MEDIUM", 2),
            ("under_review", "on_hold", "Mettre en attente", "تعليق", ["admin", "gestionnaire"], True, False, "MEDIUM", 3),
            ("on_hold", "submitted", "Re-soumettre", "إعادة تقديم", ["admin", "gestionnaire"], False, False, "LOW", 4),
            ("under_review", "validated", "Valider", "مصادقة", ["admin", "gestionnaire"], False, False, "HIGH", 5),
            ("submitted", "validated", "Valider directement", "مصادقة مباشرة", ["admin"], False, False, "HIGH", 6),
            ("validated", "paid", "Confirmer le paiement", "تأكيد الدفع", ["admin", "comptable"], False, False, "CRITICAL", 7),
            ("submitted", "rejected", "Rejeter", "رفض", ["admin", "gestionnaire"], True, True, "HIGH", 8),
            ("under_review", "rejected", "Rejeter", "رفض", ["admin", "gestionnaire"], True, True, "HIGH", 9),
            ("validated", "rejected", "Rejeter après validation", "رفض بعد المصادقة", ["admin", "comptable"], True, True, "CRITICAL", 10),
            ("draft", "cancelled", "Annuler", "إلغاء", ["admin", "gestionnaire"], False, True, "LOW", 11),
            ("submitted", "cancelled", "Annuler", "إلغاء", ["admin", "gestionnaire"], True, True, "MEDIUM", 12),
            ("on_hold", "cancelled", "Annuler", "إلغاء", ["admin", "gestionnaire"], True, True, "MEDIUM", 13),
        ],
    },
    ("medical_coverage", "MedicalCoverageVoucher"): {
        "states": [
            ("draft", "Brouillon", "مسودة", "#6B7280", True, False, 0),
            ("submitted", "Soumise", "مقدمة", "#3B82F6", False, False, 1),
            ("pending_approval", "En attente d'approbation", "في انتظار الموافقة", "#8B5CF6", False, False, 2),
            ("pending_director_approval", "En attente du directeur", "في انتظار المدير", "#EC4899", False, False, 3),
            ("validated", "Validée", "مصادق عليها", "#10B981", False, False, 4),
            ("rejected", "Rejetée", "مرفوضة", "#EF4444", False, True, 5),
            ("printed", "Imprimée", "مطبوعة", "#F59E0B", False, False, 6),
            ("closed", "Clôturée", "مغلقة", "#059669", False, True, 7),
            ("cancelled", "Annulée", "ملغاة", "#9CA3AF", False, True, 8),
        ],
        "transitions": [
            ("draft", "submitted", "Soumettre", "تقديم", ["admin", "social_agent"], False, False, "LOW", 0),
            ("submitted", "pending_approval", "Soumettre à validation", "تقديم للمصادقة", ["admin", "social_agent"], False, False, "LOW", 1),
            ("submitted", "pending_director_approval", "Escalader au directeur", "رفع للمدير", ["admin", "social_agent", "department_manager"], True, False, "HIGH", 2),
            ("pending_approval", "validated", "Valider", "مصادقة", ["admin", "department_manager"], False, False, "MEDIUM", 3),
            ("pending_approval", "rejected", "Rejeter", "رفض", ["admin", "department_manager"], True, False, "HIGH", 4),
            ("pending_approval", "pending_director_approval", "Escalader au directeur", "رفع للمدير", ["admin", "department_manager"], True, False, "HIGH", 5),
            ("pending_director_approval", "validated", "Approuver (Directeur)", "موافقة المدير", ["admin", "director"], False, False, "HIGH", 6),
            ("pending_director_approval", "rejected", "Rejeter (Directeur)", "رفض المدير", ["admin", "director"], True, False, "CRITICAL", 7),
            ("validated", "printed", "Imprimer", "طباعة", ["admin", "gestionnaire", "comptable"], False, False, "LOW", 8),
            ("printed", "closed", "Clôturer", "إغلاق", ["admin", "gestionnaire"], False, False, "LOW", 9),
            ("draft", "cancelled", "Annuler", "إلغاء", ["admin", "social_agent"], True, False, "LOW", 10),
            ("submitted", "cancelled", "Annuler", "إلغاء", ["admin", "social_agent"], True, False, "MEDIUM", 11),
            ("pending_approval", "cancelled", "Annuler", "إلغاء", ["admin"], True, False, "MEDIUM", 12),
            ("pending_director_approval", "cancelled", "Annuler", "إلغاء", ["admin"], True, False, "MEDIUM", 13),
        ],
    },
    ("medical_coverage", "MedicalCoverageRequest"): {
        "states": [
            ("draft", "Brouillon", "مسودة", "#6B7280", True, False, 0),
            ("submitted", "Soumise", "مقدمة", "#3B82F6", False, False, 1),
            ("pending_approval", "En attente d'approbation", "في انتظار الموافقة", "#8B5CF6", False, False, 2),
            ("pending_manager_approval", "En attente du chef de service", "في انتظار رئيس القسم", "#F59E0B", False, False, 3),
            ("pending_director_approval", "En attente du directeur", "في انتظار المدير", "#EC4899", False, False, 4),
            ("validated", "Validée", "مصادق عليها", "#10B981", False, False, 5),
            ("rejected", "Rejetée", "مرفوضة", "#EF4444", False, True, 6),
            ("printed", "Imprimée", "مطبوعة", "#F59E0B", False, False, 7),
            ("closed", "Clôturée", "مغلقة", "#059669", False, True, 8),
            ("cancelled", "Annulée", "ملغاة", "#9CA3AF", False, True, 9),
        ],
        "transitions": [
            ("draft", "submitted", "Soumettre", "تقديم", ["admin", "social_agent"], False, False, "LOW", 0),
            ("submitted", "validated", "Valider automatiquement", "مصادقة تلقائية", ["admin", "social_agent"], False, False, "LOW", 1),
            ("submitted", "pending_manager_approval", "Soumettre au chef de service", "تقديم لرئيس القسم", ["admin", "social_agent"], False, False, "LOW", 2),
            ("pending_manager_approval", "validated", "Approuver", "موافقة", ["admin", "department_manager"], False, False, "MEDIUM", 3),
            ("pending_manager_approval", "rejected", "Rejeter", "رفض", ["admin", "department_manager"], True, False, "HIGH", 4),
            ("pending_manager_approval", "pending_director_approval", "Escalader au directeur", "رفع للمدير", ["admin", "department_manager"], True, False, "HIGH", 5),
            ("pending_director_approval", "validated", "Approuver", "موافقة", ["admin", "director"], False, False, "HIGH", 6),
            ("pending_director_approval", "rejected", "Rejeter", "رفض", ["admin", "director"], True, False, "CRITICAL", 7),
            ("validated", "printed", "Imprimer", "طباعة", ["admin", "gestionnaire", "comptable"], False, False, "LOW", 8),
            ("printed", "closed", "Clôturer", "إغلاق", ["admin", "gestionnaire"], False, False, "LOW", 9),
            ("draft", "cancelled", "Annuler", "إلغاء", ["admin", "social_agent"], True, False, "LOW", 10),
            ("pending_manager_approval", "cancelled", "Annuler", "إلغاء", ["admin"], True, False, "MEDIUM", 11),
            ("pending_director_approval", "cancelled", "Annuler", "إلغاء", ["admin"], True, False, "MEDIUM", 12),
        ],
    },
}


def seed_workflows(apps, schema_editor):
    WorkflowState = apps.get_model("workflow", "WorkflowState")
    WorkflowTransition = apps.get_model("workflow", "WorkflowTransition")
    WorkflowTransitionRole = apps.get_model("workflow", "WorkflowTransitionRole")
    Role = apps.get_model("administration", "Role")

    for (app_label, model_name), cfg in WORKFLOWS.items():
        state_map = {}
        for i, (sid, label_fr, label_ar, color, initial, final, order) in enumerate(cfg["states"]):
            state, _ = WorkflowState.objects.get_or_create(
                app_label=app_label, model_name=model_name, state_id=sid,
                defaults={
                    "label_fr": label_fr, "label_ar": label_ar, "color": color,
                    "is_initial": initial, "is_final": final, "display_order": order,
                },
            )
            state_map[sid] = state

        for t in cfg["transitions"]:
            from_sid, to_sid, name, label_ar, role_slugs, need_reason, reversal, severity, order = t
            from_state = state_map[from_sid]
            to_state = state_map[to_sid]
            trans, _ = WorkflowTransition.objects.get_or_create(
                app_label=app_label, model_name=model_name,
                from_state=from_state, to_state=to_state,
                defaults={
                    "name": name, "label_fr": name, "label_ar": label_ar,
                    "requires_reason": need_reason, "is_reversal": reversal,
                    "severity": severity, "display_order": order,
                },
            )
            for slug in role_slugs:
                try:
                    role = Role.all_objects.get(slug=slug)
                    WorkflowTransitionRole.objects.get_or_create(
                        transition=trans, role=role,
                    )
                except Role.all_objects.model.DoesNotExist:
                    pass


def reverse_seed(apps, schema_editor):
    WorkflowTransitionRole = apps.get_model("workflow", "WorkflowTransitionRole")
    WorkflowTransition = apps.get_model("workflow", "WorkflowTransition")
    WorkflowState = apps.get_model("workflow", "WorkflowState")
    for app_label, model_name in [(k[0], k[1]) for k in WORKFLOWS]:
        WorkflowTransitionRole.objects.filter(
            transition__app_label=app_label, transition__model_name=model_name,
        ).delete()
        WorkflowTransition.objects.filter(app_label=app_label, model_name=model_name).delete()
        WorkflowState.objects.filter(app_label=app_label, model_name=model_name).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0002_dynamic_workflow_models"),
        ("administration", "0005_add_performance_indexes"),
    ]

    operations = [
        migrations.RunPython(seed_workflows, reverse_seed),
    ]
