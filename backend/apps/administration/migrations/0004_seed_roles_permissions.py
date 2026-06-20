from django.db import migrations


ROLES = [
    {"name": "Super Admin", "slug": "super_admin", "rank": 0, "is_system": True},
    {"name": "Administrateur", "slug": "admin", "rank": 1, "is_system": True},
    {"name": "Agent Social", "slug": "social_agent", "rank": 2, "is_system": True},
    {"name": "Chef de Service", "slug": "department_manager", "rank": 3, "is_system": True},
    {"name": "Membre de Commission", "slug": "committee_member", "rank": 4, "is_system": True},
    {"name": "Directeur", "slug": "director", "rank": 5, "is_system": True},
    {"name": "Gestionnaire RH", "slug": "gestionnaire", "rank": 6, "is_system": True},
    {"name": "Comptable", "slug": "comptable", "rank": 7, "is_system": True},
    {"name": "Consultant", "slug": "consultant", "rank": 8, "is_system": True},
    {"name": "Lecture Seule", "slug": "read_only", "rank": 9, "is_system": True},
]

PERMISSIONS = [
    # ── Administration ──────────────────────────────────
    {"codename": "admin.access", "name": "Accès au module Administration", "module": "admin"},
    {"codename": "admin.manage_users", "name": "Gérer les utilisateurs", "module": "admin"},
    {"codename": "admin.manage_roles", "name": "Gérer les rôles", "module": "admin"},
    {"codename": "admin.manage_permissions", "name": "Gérer les permissions", "module": "admin"},
    {"codename": "admin.manage_system_params", "name": "Gérer les paramètres système", "module": "admin"},
    {"codename": "admin.view_audit_logs", "name": "Consulter le journal d'audit", "module": "admin"},
    {"codename": "admin.manage_workflow", "name": "Configurer les workflows", "module": "admin"},
    {"codename": "admin.manage_approval_matrix", "name": "Gérer la matrice d'approbation", "module": "admin"},

    # ── Employés ────────────────────────────────────────
    {"codename": "employee.view", "name": "Consulter les employés", "module": "employees"},
    {"codename": "employee.create", "name": "Créer des employés", "module": "employees"},
    {"codename": "employee.update", "name": "Modifier des employés", "module": "employees"},
    {"codename": "employee.delete", "name": "Supprimer des employés", "module": "employees"},
    {"codename": "employee.import", "name": "Importer des employés", "module": "employees"},
    {"codename": "employee.export", "name": "Exporter des employés", "module": "employees"},

    # ── Ayants Droit ────────────────────────────────────
    {"codename": "beneficiary.view", "name": "Consulter les ayants droit", "module": "beneficiaries"},
    {"codename": "beneficiary.create", "name": "Créer des ayants droit", "module": "beneficiaries"},
    {"codename": "beneficiary.update", "name": "Modifier des ayants droit", "module": "beneficiaries"},
    {"codename": "beneficiary.delete", "name": "Supprimer des ayants droit", "module": "beneficiaries"},

    # ── Prestations ─────────────────────────────────────
    {"codename": "benefit.view", "name": "Consulter les prestations", "module": "benefits"},
    {"codename": "benefit.create", "name": "Créer des prestations", "module": "benefits"},
    {"codename": "benefit.update", "name": "Modifier des prestations", "module": "benefits"},
    {"codename": "benefit.approve", "name": "Approuver des prestations", "module": "benefits"},
    {"codename": "benefit.reject", "name": "Rejeter des prestations", "module": "benefits"},
    {"codename": "benefit.process_payment", "name": "Traiter les paiements", "module": "benefits"},

    # ── Prêts ───────────────────────────────────────────
    {"codename": "loan.view", "name": "Consulter les prêts", "module": "loans"},
    {"codename": "loan.create", "name": "Créer des prêts", "module": "loans"},
    {"codename": "loan.update", "name": "Modifier des prêts", "module": "loans"},
    {"codename": "loan.approve", "name": "Approuver des prêts", "module": "loans"},
    {"codename": "loan.reject", "name": "Rejeter des prêts", "module": "loans"},
    {"codename": "loan.process_payment", "name": "Traiter les paiements de prêts", "module": "loans"},
    {"codename": "loan.manage", "name": "Gestion complète des prêts", "module": "loans"},

    # ── Couverture Médicale ─────────────────────────────
    {"codename": "coverage.view", "name": "Consulter les demandes de couverture", "module": "medical_coverage"},
    {"codename": "coverage.create", "name": "Créer des demandes de couverture", "module": "medical_coverage"},
    {"codename": "coverage.update", "name": "Modifier des demandes", "module": "medical_coverage"},
    {"codename": "coverage.validate", "name": "Valider automatiquement", "module": "medical_coverage"},
    {"codename": "coverage.approve_as_manager", "name": "Approuver en tant que chef de service", "module": "medical_coverage"},
    {"codename": "coverage.approve_as_director", "name": "Approuver en tant que directeur", "module": "medical_coverage"},
    {"codename": "coverage.escalate", "name": "Escalader au directeur", "module": "medical_coverage"},
    {"codename": "coverage.reject", "name": "Rejeter des demandes", "module": "medical_coverage"},
    {"codename": "coverage.print_voucher", "name": "Imprimer les bons", "module": "medical_coverage"},

    # ── Conventions ─────────────────────────────────────
    {"codename": "convention.view", "name": "Consulter les conventions", "module": "conventions"},
    {"codename": "convention.create", "name": "Créer des conventions", "module": "conventions"},
    {"codename": "convention.update", "name": "Modifier des conventions", "module": "conventions"},
    {"codename": "convention.delete", "name": "Supprimer des conventions", "module": "conventions"},

    # ── Partenaires ─────────────────────────────────────
    {"codename": "partner.view", "name": "Consulter les partenaires", "module": "conventions"},
    {"codename": "partner.create", "name": "Créer des partenaires", "module": "conventions"},
    {"codename": "partner.update", "name": "Modifier des partenaires", "module": "conventions"},
    {"codename": "partner.delete", "name": "Supprimer des partenaires", "module": "conventions"},

    # ── Finance ─────────────────────────────────────────
    {"codename": "finance.view", "name": "Consulter les finances", "module": "finance"},
    {"codename": "finance.create_budget", "name": "Gérer les budgets", "module": "finance"},
    {"codename": "finance.process_payment", "name": "Traiter les paiements", "module": "finance"},
    {"codename": "finance.export", "name": "Exporter les données financières", "module": "finance"},

    # ── Rapports ────────────────────────────────────────
    {"codename": "report.view", "name": "Consulter les rapports", "module": "reports"},
    {"codename": "report.create", "name": "Générer des rapports", "module": "reports"},
    {"codename": "report.export", "name": "Exporter des rapports", "module": "reports"},
    {"codename": "report.schedule", "name": "Planifier des rapports", "module": "reports"},

    # ── Analytics ───────────────────────────────────────
    {"codename": "analytics.view", "name": "Consulter les analytics", "module": "analytics"},
    {"codename": "analytics.decisions", "name": "Accéder aux décisions IA", "module": "analytics"},
    {"codename": "analytics.anomalies", "name": "Détecter les anomalies", "module": "analytics"},
]

ROLE_PERMISSIONS = {
    "super_admin": [p["codename"] for p in PERMISSIONS],
    "admin": [p["codename"] for p in PERMISSIONS],
    "social_agent": [
        "employee.view", "employee.create", "employee.update",
        "beneficiary.view", "beneficiary.create", "beneficiary.update",
        "benefit.view", "benefit.create",
        "loan.view", "loan.create",
        "coverage.view", "coverage.create", "coverage.update", "coverage.print_voucher",
        "convention.view", "partner.view",
        "report.view",
    ],
    "department_manager": [
        "employee.view", "employee.create", "employee.update",
        "beneficiary.view", "beneficiary.create", "beneficiary.update",
        "benefit.view", "benefit.create", "benefit.approve", "benefit.reject",
        "loan.view", "loan.create", "loan.approve", "loan.reject",
        "coverage.view", "coverage.create", "coverage.validate",
        "coverage.approve_as_manager", "coverage.escalate",
        "coverage.reject", "coverage.print_voucher",
        "convention.view", "partner.view",
        "finance.view",
        "report.view", "report.create",
    ],
    "committee_member": [
        "coverage.view", "coverage.approve_as_manager",
        "loan.view", "loan.approve",
        "benefit.view", "benefit.approve",
        "report.view",
    ],
    "director": [
        "employee.view",
        "beneficiary.view",
        "benefit.view", "benefit.approve", "benefit.reject",
        "loan.view", "loan.approve", "loan.reject",
        "coverage.view", "coverage.approve_as_director",
        "coverage.reject", "coverage.print_voucher",
        "convention.view", "convention.create", "convention.update",
        "partner.view", "partner.create", "partner.update",
        "finance.view",
        "report.view", "report.create", "report.export",
        "analytics.view",
    ],
    "gestionnaire": [
        "employee.view", "employee.create", "employee.update", "employee.export",
        "beneficiary.view", "beneficiary.create", "beneficiary.update",
        "benefit.view", "benefit.create", "benefit.approve", "benefit.reject",
        "loan.view", "loan.create", "loan.approve", "loan.reject",
        "coverage.view", "coverage.create", "coverage.validate",
        "coverage.approve_as_manager", "coverage.escalate",
        "coverage.reject", "coverage.print_voucher",
        "convention.view", "convention.create", "convention.update",
        "partner.view", "partner.create", "partner.update",
        "finance.view",
        "report.view", "report.create",
    ],
    "comptable": [
        "employee.view",
        "benefit.view", "benefit.process_payment",
        "loan.view", "loan.process_payment",
        "coverage.view", "coverage.print_voucher",
        "convention.view",
        "finance.view", "finance.create_budget", "finance.process_payment", "finance.export",
        "report.view", "report.create", "report.export",
    ],
    "consultant": [
        "employee.view",
        "beneficiary.view",
        "benefit.view",
        "loan.view",
        "coverage.view",
        "convention.view",
        "finance.view",
        "report.view",
        "analytics.view",
    ],
    "read_only": [
        "employee.view",
        "beneficiary.view",
        "benefit.view",
        "loan.view",
        "coverage.view",
        "convention.view",
        "report.view",
    ],
}


def seed_roles_permissions(apps, schema_editor):
    Role = apps.get_model("administration", "Role")
    Permission = apps.get_model("administration", "Permission")
    RolePermission = apps.get_model("administration", "RolePermission")

    created_roles = {}
    for r in ROLES:
        role, _ = Role.all_objects.get_or_create(slug=r["slug"], defaults=r)
        created_roles[role.slug] = role

    created_permissions = {}
    for p in PERMISSIONS:
        perm, _ = Permission.all_objects.get_or_create(
            codename=p["codename"], defaults=p
        )
        created_permissions[perm.codename] = perm

    for role_slug, codenames in ROLE_PERMISSIONS.items():
        role = created_roles.get(role_slug)
        if not role:
            continue
        for codename in codenames:
            perm = created_permissions.get(codename)
            if perm:
                RolePermission.all_objects.get_or_create(
                    role=role, permission=perm,
                )


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0003_historicalapprovalmatrix_historicalpermission_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_roles_permissions, reverse_seed),
    ]
