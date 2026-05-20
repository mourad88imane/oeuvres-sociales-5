# API — Aperçu

## Version
Toutes les routes sont préfixées par `/api/v1/`.

## Authentification
JWT (JSON Web Token) — deux tokens :
- `access_token` : 30 minutes (configurable)
- `refresh_token` : 7 jours

```
POST /api/v1/auth/login/
Body: { "email": "...", "password": "..." }
Response: { "access": "...", "refresh": "..." }
```

## Modules

### Auth (`/api/v1/auth/`)
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/login/` | Connexion |
| POST | `/logout/` | Déconnexion |
| POST | `/refresh/` | Rafraîchir token |
| POST | `/verify/` | Vérifier token |

### Utilisateurs (`/api/v1/users/`)
CRUD complet avec filtres, recherche, pagination.

### Prestations sociales (`/api/v1/benefits/`)
CRUD + workflow d'approbation.

### Finance (`/api/v1/finance/`)
Lignes budgétaires, paiements, reporting.

### AI & Analytics (`/api/v1/ai/`)
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/predictions/` | Prédictions enregistrées |
| POST | `/forecast/` | Générer prévision |
| POST | `/detect-anomalies/` | Détection d'anomalies |
| POST | `/score-benefit/` | Score de prestation |
| POST | `/recommendations/` | Recommandations |
| POST | `/assistant/` | Assistant IA |
| POST | `/pipeline/` | Exécuter pipeline IA |
| POST | `/behavior-analysis/` | Analyse comportementale |
| POST | `/segmentation/` | Segmentation utilisateurs |

### Monitoring (`/api/v1/monitoring/`)
Métriques, logs, santé des services.

### Audit (`/api/v1/audit/`)
Trail d'audit, validation trace.

## Pagination
Toutes les listes sont paginées (25 items/page par défaut).
```
GET /api/v1/users/?page=1&page_size=50
```

## Format Réponse
```json
{
    "status": "success",
    "data": { ... },
    "message": "Optionnel"
}
```

## Codes d'Erreur
| Code | Signification |
|------|---------------|
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 404 | Ressource introuvable |
| 422 | Validation échouée |
| 429 | Trop de requêtes |
| 500 | Erreur serveur |

## Documentation Interactive
- Swagger : `/api/docs/`
- ReDoc : `/api/redoc/`
- Schéma OpenAPI : `/api/schema/`
