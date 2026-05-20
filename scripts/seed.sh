#!/usr/bin/env bash
# ============================================================
# SEED — Peuplement rapide de données de démonstration
# ============================================================
# Usage: ./scripts/seed.sh
# ============================================================
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
BACKEND="docker compose -f $COMPOSE_FILE exec -T backend"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   Seed — Données de démonstration             ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

$BACKEND python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.benefits.models import Benefit, BenefitType
from apps.conventions.models import Convention, Partner
from apps.finance.models import BudgetLine, Payment
from apps.employees.models import Employee
from apps.beneficiaries.models import Beneficiary
from shared.registry.models import WorkflowRegistration

User = get_user_model()

# ── Admin ─────────────────────────────────────────────────
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@oeuvres.dz", "admin123")
    print("✓ Admin créé (admin/admin123)")

# ── Gestionnaire ──────────────────────────────────────────
if not User.objects.filter(username="gestionnaire").exists():
    User.objects.create_user("gestionnaire", "gest@oeuvres.dz", "gest123", role="gestionnaire")
    print("✓ Gestionnaire créé")

# ── Types de prestations ─────────────────────────────────
for name, code in [("Aide scolaire", "SCOLAIRE"), ("Allocation familiale", "FAMILIALE"),
                    ("Aide médicale", "MEDICALE"), ("Aide logement", "LOGEMENT"),
                    ("Prime naissance", "NAISSANCE"), ("Aide décès", "DECES")]:
    BenefitType.objects.get_or_create(name=name, code=code)
print(f"✓ Types de prestations ({BenefitType.objects.count()})")

# ── Directions ───────────────────────────────────────────
for name, code in [("Direction Générale", "DG"), ("RH", "RH"),
                    ("Finances", "FIN"), ("Médical", "MED")]:
    Department.objects.get_or_create(name=name, code=code)
print(f"✓ Directions ({Department.objects.count()})")

# ── Partenaires ──────────────────────────────────────────
for name in ["Pharmacie Centrale", "Clinique El-Djazair", "École Privée Les Pins",
             "Mutuelle SOMATHEZ", "Caisse Nationale CNAS"]:
    Partner.objects.get_or_create(name=name, contact_email=f"contact@{name.lower().replace(' ', '')}.dz")
print(f"✓ Partenaires ({Partner.objects.count()})")

# ── Conventions ──────────────────────────────────────────
dept = Department.objects.first()
partner = Partner.objects.first()
Convention.objects.get_or_create(
    title="Convention cadre 2025",
    defaults={
        "partner": partner,
        "department": dept,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "amount": 5000000,
        "status": "active",
    }
)
print(f"✓ Conventions ({Convention.objects.count()})")

# ── Budget ───────────────────────────────────────────────
bt = BenefitType.objects.first()
BudgetLine.objects.get_or_create(
    year=2025,
    benefit_type=bt,
    defaults={
        "allocated_amount": 15000000,
        "spent_amount": 8500000,
        "department": dept,
    }
)
print(f"✓ Budget ({BudgetLine.objects.count()})")

# ── Employés ─────────────────────────────────────────────
for i in range(5):
    Employee.objects.get_or_create(
        registration_number=f"EMP{i:04d}",
        defaults={
            "first_name": f"Employe{i}",
            "last_name": f"Test{i}",
            "email": f"employe{i}@oeuvres.dz",
            "department": dept,
            "grade": f"Grade {chr(65+i)}",
            "gross_salary": 30000 + (i * 5000),
        }
    )
print(f"✓ Employés ({Employee.objects.count()})")

# ── Bénéficiaires avec prestations ───────────────────────
for i in range(3):
    emp = Employee.objects.filter(department=dept).first()
    if emp:
        Ben, _ = Beneficiary.objects.get_or_create(
            registration_number=f"BEN{i:04d}",
            defaults={
                "first_name": f"Bene{i}",
                "last_name": f"Test{i}",
                "employee": emp,
                "relationship": "conjoint" if i == 0 else "enfant",
            }
        )
        Benefit.objects.get_or_create(
            beneficiary=Ben,
            benefit_type=bt,
            defaults={
                "amount": 15000 + (i * 2000),
                "status": "approved",
                "request_date": "2025-01-15",
                "decision_date": "2025-01-20",
            }
        )
print(f"✓ Bénéficiaires ({Beneficiary.objects.count()})")
print(f"✓ Prestations ({Benefit.objects.count()})")

print()
print("✅ Données de démonstration créées avec succès")
EOF
