"""
Management command : python manage.py seed_data
Peuple la base avec des données de test réalistes.
"""

import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEPARTMENTS = [
    ("DG", "Direction Générale", None),
    ("RH", "Ressources Humaines", "DG"),
    ("FIN", "Finance et Comptabilité", "DG"),
    ("TECH", "Direction Technique", "DG"),
    ("INFO", "Informatique", "TECH"),
    ("ADM", "Administration", "DG"),
    ("COM", "Communication", "DG"),
]

FIRST_NAMES_M = [
    "Ahmed",
    "Mohammed",
    "Karim",
    "Youcef",
    "Hocine",
    "Sofiane",
    "Farouk",
    "Rachid",
    "Omar",
    "Salim",
]
FIRST_NAMES_F = [
    "Fatima",
    "Amina",
    "Leila",
    "Nassima",
    "Meriem",
    "Samira",
    "Karima",
    "Nadia",
    "Sara",
    "Wafa",
]
LAST_NAMES = [
    "Benali",
    "Kaci",
    "Amari",
    "Meziane",
    "Taleb",
    "Ferhat",
    "Ouali",
    "Cherif",
    "Hadj",
    "Bensalem",
]

JOBS = [
    ("Ingénieur principal", "A", 8),
    ("Ingénieur", "A", 5),
    ("Technicien supérieur", "B", 6),
    ("Technicien", "B", 4),
    ("Chef de service", "A", 9),
    ("Agent administratif", "C", 3),
    ("Comptable", "B", 5),
    ("Analyste financier", "B", 6),
    ("Responsable RH", "A", 7),
    ("Gestionnaire", "B", 5),
]


class Command(BaseCommand):
    help = "Peuple la base avec des données de test"

    def add_arguments(self, parser):
        parser.add_argument(
            "--employees", type=int, default=30, help="Nombre d'employés à créer (défaut: 30)"
        )
        parser.add_argument(
            "--clear", action="store_true", help="Supprimer les données existantes avant de seeder"
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        self.stdout.write("🌱 Démarrage du seeding...")
        admin = self._create_users()
        depts = self._create_departments(admin)
        self._create_employees(depts, admin, options["employees"])
        self.stdout.write(self.style.SUCCESS("✅ Seeding terminé avec succès !"))

    def _clear(self):
        from apps.beneficiaries.models import Beneficiary
        from apps.departments.models import Department
        from apps.employees.models import Employee

        Beneficiary.all_objects.all().delete()
        Employee.all_objects.all().delete()
        Department.all_objects.all().delete()
        User.objects.filter(email__contains="@test.dz").delete()
        self.stdout.write("🗑️  Données existantes supprimées")

    def _create_users(self):
        users = {}
        for email, role, fname, lname in [
            ("admin@oeuvres.dz", "admin", "Admin", "Système"),
            ("gestionnaire@oeuvres.dz", "gestionnaire", "Gestionnaire", "RH"),
            ("comptable@oeuvres.dz", "comptable", "Comptable", "Finance"),
            ("consultant@oeuvres.dz", "consultant", "Consultant", "Externe"),
        ]:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": fname,
                    "last_name": lname,
                    "role": role,
                    "is_active": True,
                    "must_change_password": False,
                },
            )
            if created:
                user.set_password("Password123!")
                user.save()
                self.stdout.write(f"  👤 {role}: {email} / Password123!")
            users[role] = user

        # Superuser
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email="superadmin@oeuvres.dz",
                password="SuperAdmin123!",
                first_name="Super",
                last_name="Admin",
            )
            self.stdout.write("  🔑 Superadmin: superadmin@oeuvres.dz / SuperAdmin123!")

        return users["admin"]

    def _create_departments(self, admin):
        from apps.departments.models import Department

        dept_map = {}
        for code, name, parent_code in DEPARTMENTS:
            parent = dept_map.get(parent_code)
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "parent": parent,
                    "is_active": True,
                    "created_by": admin,
                },
            )
            dept_map[code] = dept
            if created:
                self.stdout.write(f"  🏢 Département créé : {code} — {name}")
        return dept_map

    def _create_employees(self, depts, admin, count):
        from apps.beneficiaries.models import Beneficiary
        from apps.employees.models import Employee

        dept_list = [d for k, d in depts.items() if k != "DG"]
        created_count = 0

        for i in range(count):
            gender = random.choice(["M", "F"])
            fname = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
            lname = random.choice(LAST_NAMES)
            job, grade, level = random.choice(JOBS)
            dept = random.choice(dept_list)
            dob = date.today() - timedelta(days=random.randint(25 * 365, 58 * 365))
            hired = dob + timedelta(days=random.randint(22 * 365, 35 * 365))
            if hired > date.today():
                hired = date.today() - timedelta(days=random.randint(30, 365))
            status = random.choices(
                ["active", "active", "active", "inactive", "retired"],
                weights=[70, 10, 10, 5, 5],
            )[0]

            emp, created = Employee.objects.get_or_create(
                email_professional=f"{fname.lower()}.{lname.lower()}{i}@oeuvres.dz",
                defaults={
                    "first_name": fname,
                    "last_name": lname,
                    "gender": gender,
                    "date_of_birth": dob,
                    "department": dept,
                    "job_title": job,
                    "grade": f"Grade {grade}",
                    "grade_level": level,
                    "contract_type": random.choice(["cdi", "cdi", "cdd"]),
                    "date_hired": hired,
                    "status": status,
                    "phone": f"+213 {random.randint(500,799)} {random.randint(100,999)} {random.randint(100,999)}",
                    "wilaya": random.choice(
                        ["Alger", "Oran", "Constantine", "Annaba", "Blida", "Sétif"]
                    ),
                    "city": random.choice(["Alger", "Oran", "Constantine", "Annaba"]),
                    "marital_status": random.choice(["single", "married", "married", "divorced"]),
                    "nationality": "Algérienne",
                    "education_level": random.choice(
                        ["Bac+5", "Ingénieur", "Master", "Licence", "BTS"]
                    ),
                    "created_by": admin,
                },
            )

            if not created:
                continue

            created_count += 1

            # Ajouter des ayants droit aléatoires
            if emp.marital_status == "married" and random.random() > 0.3:
                spouse_gender = "F" if gender == "M" else "M"
                spouse_names = FIRST_NAMES_F if spouse_gender == "F" else FIRST_NAMES_M
                Beneficiary.objects.create(
                    employee=emp,
                    first_name=random.choice(spouse_names),
                    last_name=lname,
                    gender=spouse_gender,
                    date_of_birth=dob + timedelta(days=random.randint(-3 * 365, 3 * 365)),
                    relationship="spouse",
                    created_by=admin,
                )

            # Enfants
            num_children = random.choice([0, 0, 1, 2, 3])
            for _j in range(num_children):
                child_age = random.randint(1, 28)
                cdob = date.today() - timedelta(days=child_age * 365)
                is_student = child_age >= 18 and random.random() > 0.4
                Beneficiary.objects.create(
                    employee=emp,
                    first_name=random.choice(FIRST_NAMES_M + FIRST_NAMES_F),
                    last_name=lname,
                    gender=random.choice(["M", "F"]),
                    date_of_birth=cdob,
                    relationship="child",
                    is_student=is_student,
                    created_by=admin,
                )

        self.stdout.write(f"  👥 {created_count} employés créés avec leurs ayants droit")


def seed_benefits(emp_list, admin_user):
    """Ajouter des données de test pour les prestations."""
    import random

    from apps.benefits.models import Benefit, BenefitType
    from apps.benefits.services import BenefitService

    svc = BenefitService()

    types = [
        ("MED01", "Prise en charge médicale", "medical", 100000, 1),
        ("AID01", "Aide exceptionnelle", "aid", 50000, 0),
        ("PRET01", "Prêt social", "loan", 500000, 2),
        ("SCO01", "Aide scolarité", "aid", 30000, 0),
        ("PRM01", "Prime annuelle", "bonus", 80000, 0),
    ]
    type_objs = []
    for code, name, cat, maxamt, minseni in types:
        t, _ = BenefitType.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "category": cat,
                "max_amount": maxamt,
                "min_seniority_years": minseni,
                "target_processing_days": 5,
                "is_active": True,
                "created_by": admin_user,
            },
        )
        type_objs.append(t)

    statuses = ["draft", "submitted", "validated", "paid", "rejected"]
    counts = [20, 30, 10, 30, 10]

    for emp in emp_list[:20]:
        btype = random.choice(type_objs)
        amount = random.randint(10000, int(btype.max_amount or 50000))
        state = random.choices(statuses, weights=counts)[0]
        b = Benefit.objects.create(
            employee=emp,
            benefit_type=btype,
            title=f"{btype.name} — {emp.get_full_name()}",
            requested_amount=amount,
            priority=random.choice(["low", "normal", "normal", "high"]),
            workflow_state="draft",
            created_by=admin_user,
        )
        try:
            if state in ("submitted", "validated", "paid", "rejected"):
                svc.transition(b, "submitted", user=admin_user)
            if state in ("validated", "paid"):
                svc.transition(b, "under_review", user=admin_user)
                svc.transition(
                    b, "validated", user=admin_user, metadata={"approved_amount": float(amount)}
                )
            if state == "paid":
                svc.transition(
                    b,
                    "paid",
                    user=admin_user,
                    metadata={
                        "payment_reference": f"VIR-TEST-{b.reference}",
                        "paid_amount": float(amount),
                    },
                )
            if state == "rejected":
                svc.transition(b, "rejected", user=admin_user, reason="Dossier incomplet")
        except Exception:
            pass
