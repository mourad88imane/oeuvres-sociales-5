# Plan d'Architecture Enterprise — Oeuvres Sociales

> Version 1.0 — Mai 2026
> Stratégie de transformation vers une architecture microservices cloud-ready,
> event-driven, hautement disponible et scalable.

---

## Table des matières

1. [Vision Architecture](#1-vision-architecture)
2. [Bounded Contexts & Service Decoupling](#2-bounded-contexts--service-decoupling)
3. [API Gateway & Routing](#3-api-gateway--routing)
4. [Event-Driven Architecture](#4-event-driven-architecture)
5. [Message Broker](#5-message-broker)
6. [Scalabilité Horizontale](#6-scalabilité-horizontale)
7. [Haute Disponibilité](#7-haute-disponibilité)
8. [Sécurité Avancée](#8-sécurité-avancée)
9. [Stratégie de Migration Progressive](#9-stratégie-de-migration-progressive)
10. [Optimisation Performance](#10-optimisation-performance)
11. [Architecture Cloud-Ready](#11-architecture-cloud-ready)
12. [Roadmap & Priorisation](#12-roadmap--priorisation)

---

## 1. Vision Architecture

### 1.1 État actuel (Monolithe Django)

```
┌─────────────────────────────────────────────────────┐
│                   Nginx (Reverse Proxy)              │
├─────────────────────────────────────────────────────┤
│                   Django Monolith                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │ Auth │ │Users │ │Employees│ │Finance│ │ Benefits │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │Conv. │ │Report│ │  AI  │ │Monit.│ │Shared    │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │
├─────────────────────────────────────────────────────┤
│           PostgreSQL (1 instance)                    │
├─────────────────────────────────────────────────────┤
│                  Redis (Cache + Broker)              │
└─────────────────────────────────────────────────────┘
```

### 1.2 Architecture cible (Microservices)

```
                    ┌──────────┐
                    │  Client  │ (React SPA + Mobile)
                    └────┬─────┘
                         │ HTTPS
                    ┌────▼─────┐
                    │CloudFront │ CDN + WAF
                    │  / ALB   │
                    └────┬─────┘
                         │
                    ┌────▼──────────────────────┐
                    │     API Gateway (Kong)     │
                    │  Auth / Rate Limit / mTLS │
                    │  Routing / Transformation │
                    └────┬────┬────┬────┬────┬──┘
                         │    │    │    │    │
              ┌──────────┘    │    │    │    └──────────┐
              │               │    │    │               │
         ┌────▼───┐    ┌──────▼──┐ │ ┌──▼──────┐  ┌────▼───┐
         │  Auth  │    │  Core   │ │ │Reporting│  │   AI   │
         │ Service│    │ Business│ │ │ Service │  │ Service│
         └────┬───┘    │ Service │ │ └────┬────┘  └────┬───┘
              │        └────┬─────┘ │     │            │
              │             │       │     │            │
              │    ┌────────▼──┐ ┌──▼─────▼──┐        │
              │    │ Employee │ │  Finance  │         │
              │    │ Service  │ │  Service  │         │
              │    └────┬─────┘ └────┬──────┘         │
              │         │            │                │
              │    ┌────▼─────┐ ┌────▼──────┐         │
              │    │ Benefits │ │Convention │         │
              │    │ Service  │ │  Service  │         │
              │    └──────────┘ └───────────┘         │
              │                                       │
              └──────────┬────────────────────────────┘
                         │
                    ┌────▼─────────────────────────────┐
                    │     Message Broker (RabbitMQ)     │
                    │  Event Bus / Commands / Sagas     │
                    └────┬───────────────────────────┬──┘
                         │                           │
                    ┌────▼─────┐              ┌──────▼──┐
                    │PostgreSQL│              │ Redis   │
                    │(1 write  │              │ Cache + │
                    │ + N read │              │ Session │
                    │ replicas)│              └─────────┘
                    └──────────┘
```

### 1.3 Principes directeurs

| Principe | Application |
|---|---|
| **12-Factor App** | Codebase unique, dépendances explicites, config dans l'environnement |
| **Domain-Driven Design** | Bounded contexts alignés sur les domaines métier |
| **Event-Driven** | Communication asynchrone via événements, pas d'appels synchrones cross-service |
| **Strangler Fig** | Migration incrémentale sans réécriture |
| **Zero-Trust Security** | mTLS, JWT court, RBAC + ABAC, audit immuable |
| **Stateless** | Chaque service sans état local, session en Redis |
| **Observability First** | Logs structurés, métriques Prometheus, tracing OpenTelemetry |

---

## 2. Bounded Contexts & Service Decoupling

### 2.1 Découpage en services

Basé sur l'audit des dépendances actuelles (FK croisés), voici les **8 bounded contexts** :

| # | Service | Responsabilité | Dépend actuelles | Base de données |
|---|---|---|---|---|
| **S1** | **Identity & Access** | Auth JWT, users, rôles, permissions, sessions | Aucune (indépendant) | `identity_db` (PostgreSQL) |
| **S2** | **Employee Management** | Employés, départements, hiérarchie, bénéficiaires | S1 (created_by) | `employee_db` |
| **S3** | **Benefits Management** | Prestations, types, workflow, pièces jointes | S1, S2 | `benefits_db` |
| **S4** | **Finance & Accounting** | Budgets, paiements, écritures comptables, exercices fiscaux | S1, S2, S3 | `finance_db` |
| **S5** | **Convention Management** | Partenaires, conventions, documents, alertes | S1 | `conventions_db` |
| **S6** | **Reporting & Analytics** | KPIs, rapports, exports, tableaux de bord | S1, S2, S3, S4, S5 (lecture seule via events) | `reporting_db` |
| **S7** | **AI & Intelligence** | Scoring, anomalies, recommandations, forecasting, assistant | S1, S2, S3, S4 (lecture via events + API) | `ai_db` |
| **S8** | **Notification** | Notifications in-app, email, push, digests | S1, S3, S5 (events) | `notifications_db` |

### 2.2 Stratégie de base de données

```
┌─────────────────────────────────────────────────────┐
│                  Database per Service                │
│                                                     │
│  S1: identity_db  ──── Aucune FK externe            │
│  S2: employee_db  ──── FK interne seulement         │
│  S3: benefits_db  ──── stocke employee_id (pas FK)  │
│  S4: finance_db   ──── stocke employee_id,          │
│                        benefit_id (pas FK)          │
│  S5: conventions_db ── Aucune FK externe            │
│  S6: reporting_db  ── Materialized views locales    │
│  S7: ai_db         ── Feature store + predictions   │
│  S8: notifications_db ── FK -> user_id (via S1 API) │
└─────────────────────────────────────────────────────┘
```

**Règle :** Aucun ForeignKey entre services. Chaque service stocke les IDs référencés comme `VARCHAR` (pas de contrainte référentielle cross-DB). L'intégrité est assurée par des **sagas** et **eventual consistency**.

### 2.3 API contractuelle entre services

Chaque service expose :
- **REST API** (synchronisé) pour les requêtes temps réel (CRUD)
- **gRPC** (interne) pour les appels à haut débit entre services
- **Événements** (asynchrone) pour la propagation des changements d'état

```
Service A ──POST /api/v1/resource──► Service A DB
     │
     ├──► Event: resource.created ──► Message Broker
     │                                   │
     │                          ┌────────▼────────┐
     │                          │  Service B      │
     │                          │  (consomme event)│
     │                          └─────────────────┘
```

---

## 3. API Gateway & Routing

### 3.1 Architecture Gateway

```
                   ┌─────────────────────┐
                   │   Kong API Gateway   │
                   │  (Kong Ingress + K8s)│
                   ├─────────────────────┤
                   │  Plugins:           │
                   │  • JWT Validation   │
                   │  • Rate Limiting    │
                   │  • IP Restriction   │
                   │  • CORS             │
                   │  • Request Transform│
                   │  • Prometheus       │
                   │  • Correlation ID   │
                   └──────────┬──────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────▼────┐         ┌────▼────┐         ┌─────▼────┐
    │ Service │         │ Service │         │ Service  │
    │   S1    │         │  S2-S5  │         │ S6-S8    │
    └─────────┘         └─────────┘         └──────────┘
```

### 3.2 Routage

| Route | Service cible | Auth | Rate Limit |
|---|---|---|---|
| `/api/v1/auth/*` | Identity (S1) | Aucun (public) | 5/m login, 30/m reste |
| `/api/v1/users/*` | Identity (S1) | JWT + RBAC | 100/m |
| `/api/v1/employees/*` | Employee (S2) | JWT + RBAC | 100/m |
| `/api/v1/benefits/*` | Benefits (S3) | JWT + RBAC | 100/m |
| `/api/v1/finance/*` | Finance (S4) | JWT + RBAC | 100/m |
| `/api/v1/conventions/*` | Convention (S5) | JWT + RBAC | 100/m |
| `/api/v1/reporting/*` | Reporting (S6) | JWT + RBAC | 200/m |
| `/api/v1/ai/*` | AI (S7) | JWT + RBAC | 50/m |
| `/api/v1/notifications/*` | Notification (S8) | JWT | 200/m |
| `/admin/*` | Admin panel (tous) | JWT + admin | 30/m |
| `/api/docs/*` | Documentation | Aucun | 10/m |

### 3.3 Kong Configuration (exemple)

```yaml
# kong.yaml
_format_version: "3.0"
services:
  - name: identity-service
    url: http://identity-svc:8000
    routes:
      - name: auth-routes
        paths:
          - /api/v1/auth
          - /api/v1/users
        plugins:
          - name: rate-limiting
            config:
              minute: 100
          - name: jwt
            config:
              key_claim_name: "sub"
              secret_is_base64: false
  
  - name: benefits-service
    url: http://benefits-svc:8000
    routes:
      - name: benefits-routes
        paths:
          - /api/v1/benefits
        plugins:
          - name: rate-limiting
            config:
              minute: 100
          - name: correlation-id
            config:
              header_name: X-Correlation-ID
              generator: uuid
              echo_downstream: true
```

### 3.4 Circuit Breaker (Resilience4j)

```yaml
# circuit-breaker.yml
resilience4j:
  circuitbreaker:
    configs:
      default:
        slidingWindowSize: 10
        failureRateThreshold: 50
        waitDurationInOpenState: 30s
        permittedNumberOfCallsInHalfOpenState: 3
        recordExceptions:
          - java.io.IOException
          - java.util.concurrent.TimeoutException
```

---

## 4. Event-Driven Architecture

### 4.1 Catalogue d'événements métier

#### Événements de domaine (Domain Events)

| Événement | Publisher | Consommateurs | Payload clé |
|---|---|---|---|
| `employee.hired` | Employee (S2) | Benefits, Finance, Reporting, AI, Notification | employee_id, department_id, date_hired |
| `employee.updated` | Employee (S2) | Benefits, Finance, Reporting, AI | employee_id, changed_fields |
| `employee.terminated` | Employee (S2) | Benefits, Finance, AI | employee_id, reason, date |
| `benefit.submitted` | Benefits (S3) | Finance, Reporting, AI, Notification | benefit_id, employee_id, amount, type |
| `benefit.validated` | Benefits (S3) | Finance, Reporting, AI, Notification | benefit_id, employee_id, approved_amount |
| `benefit.paid` | Benefits (S3) | Finance, Reporting, AI, Notification | benefit_id, employee_id, amount, payment_ref |
| `benefit.rejected` | Benefits (S3) | Reporting, AI, Notification | benefit_id, reason |
| `payment.created` | Finance (S4) | Benefits, Reporting, AI | payment_id, benefit_id, amount |
| `payment.completed` | Finance (S4) | Benefits, Reporting, AI, Notification | payment_id, benefit_id, amount, batch_ref |
| `budget.alert` | Finance (S4) | AI, Notification | budget_id, consumption_pct, severity |
| `convention.expiring` | Convention (S5) | Notification, AI | convention_id, partner_id, end_date |
| `convention.signed` | Convention (S5) | Reporting, AI | convention_id, partner_id, amount |
| `kpi.anomaly` | Reporting (S6) | AI, Notification | kpi_code, value, zscore |
| `ai.recommendation.generated` | AI (S7) | Notification, Reporting | recommendation_id, domain, priority |

#### Événements système (System Events)

| Événement | Publisher | Consommateurs |
|---|---|---|
| `auth.login.succeeded` | Identity (S1) | Audit, AI (behavior) |
| `auth.login.failed` | Identity (S1) | Audit, AI (security) |
| `monitoring.endpoint.degraded` | Monitoring | Notification, Incident |
| `scheduled.report.ready` | Reporting (S6) | Notification, Email |

### 4.2 Format d'événement standardisé (CloudEvents)

```json
{
  "specversion": "1.0",
  "type": "com.oeuvressociales.benefit.submitted",
  "source": "/services/benefits/v1",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "time": "2026-05-20T14:30:00Z",
  "datacontenttype": "application/json",
  "subject": "benefit/a1b2c3d4",
  "data": {
    "benefit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "employee_id": "f0e1d2c3-b4a5-6789-0fed-cba987654321",
    "benefit_type_code": "MEDICAL_REIMBURSEMENT",
    "amount": 150000.00,
    "currency": "DZD",
    "submitted_by": "user-uuid",
    "submitted_at": "2026-05-20T14:30:00Z"
  },
  "correlationid": "corr-abc-123",
  "partitionkey": "benefit/a1b2c3d4"
}
```

### 4.3 Sagas (Transactions distribuées)

#### Saga: Traitement complet d'une prestation

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Benefits │      │ Finance  │      │   AI     │      │  Notif   │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                  │                  │                  │
     │ ① benefit.submitted ─────────────► │                  │
     │                 │                  │                  │
     │                  │  ② score.requested ──────────────►│
     │                  │                  │                  │
     │                  │  ③ score.ready ◄───────────────────│
     │                  │                  │                  │
     │  ④ budget.check.requested ───────► │                  │
     │                  │                  │                  │
     │  ⑤ budget.allocated ◄────────────── │                  │
     │                  │                  │                  │
     │  ⑥ notification.sent ◄─────────────────────────────── │
     │                  │                  │                  │
```

#### Pattern Saga : Choreography (préféré) vs Orchestration

| Pattern | Cas d'usage | Mécanisme |
|---|---|---|
| **Choreography** | Événements simples sans compensation | Chaque service publie/écoute |
| **Orchestration** | Transactions multi-étapes avec rollback | Saga Coordinator service |

**Exemple d'orchestration pour création prestation :**

```python
# Saga Coordinator
class BenefitCreationSaga:
    steps = [
        Step("reserve_budget", FinanceService, compensate="release_budget"),
        Step("score_benefit", AIService),
        Step("notify_employee", NotificationService),
        Step("update_dashboard", ReportingService),
    ]
    
    def execute(self, benefit_id):
        for step in self.steps:
            try:
                step.execute(benefit_id)
            except Exception:
                # Rollback en ordre inverse
                for executed in reversed(self.executed):
                    executed.compensate(benefit_id)
                raise SagaFailed(benefit_id)
```

---

## 5. Message Broker

### 5.1 Choix : RabbitMQ + Kafka (dual broker)

| Broker | Usage | Justification |
|---|---|---|
| **RabbitMQ** | Commandes, RPC, tâches Celery, workflows | Faible latence, routing complexe, DLQ |
| **Apache Kafka** | Event sourcing, audit log, analytics stream | Haute rétention, relecture, partitionnement |

### 5.2 Topologie RabbitMQ

```
┌────────────────────────────────────────────────┐
│              RabbitMQ Cluster                   │
│             (3 nœuds, mirrored queues)          │
├────────────────────────────────────────────────┤
│                                                 │
│  Exchanges:                                     │
│  ┌──────────────┐  ┌──────────────────────┐    │
│  │ domain-events │  │   commands           │    │
│  │ (topic)       │  │   (direct)           │    │
│  └──────┬───────┘  └───────┬──────────────┘    │
│         │                  │                    │
│  Queues:│                  │                    │
│  ┌──────▼──────┐     ┌────▼─────┐              │
│  │employee.evt │     │benefit.  │              │
│  │             │     │cmd.queue │              │
│  ├─────────────┤     ├──────────┤              │
│  │benefit.evt  │     │finance.  │              │
│  │             │     │cmd.queue │              │
│  ├─────────────┤     ├──────────┤              │
│  │finance.evt  │     │  DLQ     │              │
│  └─────────────┘     └──────────┘              │
│                                                 │
│  DLQ: dead-letter (retry 3x puis parking lot)   │
└────────────────────────────────────────────────┘
```

### 5.3 Configuration RabbitMQ

```python
# shared/eventbus/config.py
RABBITMQ_CONFIG = {
    "host": os.getenv("RABBITMQ_HOST", "rabbitmq"),
    "port": int(os.getenv("RABBITMQ_PORT", 5672)),
    "vhost": "oeuvres_sociales",
    "credentials": {
        "username": os.getenv("RABBITMQ_USER", "oeuvres"),
        "password": os.getenv("RABBITMQ_PASS"),
    },
    "heartbeat": 60,
    "blocked_connection_timeout": 30,
    "connection_attempts": 5,
    "retry_delay": 2,
}

EXCHANGES = {
    "domain-events": {
        "type": "topic",
        "durable": True,
        "arguments": {"alternate-exchange": "unrouted-events"},
    },
    "commands": {
        "type": "direct",
        "durable": True,
    },
}

# Dead Letter Queue policy
DLQ_POLICY = {
    "dead-letter-exchange": "dlx",
    "dead-letter-routing-key": "dlq",
    "message-ttl": 300000,       # 5 min
    "max-length": 10000,
    "max-retries": 3,
}
```

### 5.4 Kafka pour Event Sourcing

**Topics Kafka :**

| Topic | Partitions | Rétention | Taille max |
|---|---|---|---|
| `audit.log` | 6 | 365 jours | 500 GB |
| `event-store.benefits` | 3 | 90 jours | 100 GB |
| `event-store.finance` | 3 | 90 jours | 100 GB |
| `analytics.stream` | 6 | 30 jours | 50 GB |
| `ai.features` | 4 | 7 jours | 20 GB |

**Schema Registry (Avro) :**

```json
{
  "namespace": "com.oeuvressociales.avro",
  "type": "record",
  "name": "BenefitSubmitted",
  "fields": [
    {"name": "benefit_id", "type": "string"},
    {"name": "employee_id", "type": "string"},
    {"name": "amount", "type": "double"},
    {"name": "type_code", "type": "string"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"}
  ]
}
```

---

## 6. Scalabilité Horizontale

### 6.1 Stratégie par service

| Service | Stratégie | Scale trigger | Max replicas |
|---|---|---|---|
| **Identity (S1)** | HTTP stateless + Redis session | CPU > 70%, RAM > 80% | 6 |
| **Employee (S2)** | HTTP stateless + read replicas | CPU > 60% | 8 |
| **Benefits (S3)** | HTTP stateless + Celery workers | Queue depth > 100 | 12 |
| **Finance (S4)** | HTTP stateless + read replicas | CPU > 60%, end de mois | 10 |
| **Convention (S5)** | HTTP stateless | CPU > 70% | 4 |
| **Reporting (S6)** | HTTP + CQRS read model | Concurrence requêtes | 6 |
| **AI (S7)** | HTTP + Celery workers (GPU si ML) | Queue ML > 10 | 4 |
| **Notification (S8)** | Celery workers (IO-bound) | Queue > 1000 | 8 |

### 6.2 Mise à l'échelle automatique (Kubernetes HPA)

```yaml
# k8s/hpa-benefits.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: benefits-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: benefits-service
  minReplicas: 2
  maxReplicas: 12
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: celery_queue_depth
        target:
          type: AverageValue
          averageValue: 100
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
```

### 6.3 Base de données : Read Replicas + Sharding

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Primary    │────►│ Read Replica │────►│ Read Replica │
│  (write)    │     │ 1 (reporting)│     │ 2 (analytics)│
└──────┬──────┘     └──────────────┘     └──────────────┘
       │
       ├─────────────────────────────────────────────────┐
       │ Postgres Sharding (Citus / pg_partman)          │
       │                                                 │
       │ benefits_2024 │ benefits_2025 │ benefits_2026   │
       │ (partition par année)                           │
       └─────────────────────────────────────────────────┘
```

**Sharding strategy :**
- **Benefits** : Partitionné par année de `created_at` (range partitioning)
- **Finance** : Partitionné par `fiscal_year_id` (list partitioning)
- **AuditLog** : Partitionné par mois (range, retention rolling 365 jours)
- **AIEvent** : Partitionné par mois (range, retention 90 jours)

### 6.4 Cache multi-niveau

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  L1: Browser │      │  L2: CDN     │      │  L3: Redis   │
│  Cache       │      │  (CloudFront)│      │  Cache       │
│  5 min       │      │  1 hour      │      │  5 min       │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ Static assets│      │ API responses│      │ DB queries   │
│ Images       │      │ (GET only)   │      │ Session data  │
│              │      │ Schema docs  │      │ Rate limits   │
└──────────────┘      └──────────────┘      └──────────────┘
```

**Cache invalidation patterns :**
- **Cache-aside** (Lazy loading) : Pour les données de référence (types, départements)
- **Write-through** : Pour les sessions utilisateur
- **Event-based invalidation** : À chaque événement métier, invalidation du cache via RabbitMQ

---

## 7. Haute Disponibilité

### 7.1 Architecture multi-AZ

```
                     ┌─────────────────────────┐
                     │   Route53 (DNS)         │
                     │   Failover: 30s TTL     │
                     └────────┬────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼──────┐ ┌─────▼───────┐ ┌─────▼──────┐
     │  AZ eu-west-1a│ │eu-west-1b   │ │eu-west-1c  │
     │               │ │             │ │            │
     │ ┌───────────┐ │ │ ┌─────────┐ │ │ ┌────────┐ │
     │ │ Kong + K8s│ │ │ │ Kong+K8s│ │ │ │Kong+K8s│ │
     │ ├───────────┤ │ │ ├─────────┤ │ │ ├────────┤ │
     │ │ RabbitMQ  │ │ │ │RabbitMQ │ │ │ │RabbitMQ│ │
     │ │ (mirror)  │ │ │ │(mirror) │ │ │ │(mirror)│ │
     │ ├───────────┤ │ │ ├─────────┤ │ │ ├────────┤ │
     │ │ PostgreSQL│ │ │ │Postgres │ │ │ │Postgres│ │
     │ │ (Primary) │ │ │ │(Replica)│ │ │ │(Replica)│ │
     │ └───────────┘ │ │ └─────────┘ │ │ └────────┘ │
     └───────────────┘ └─────────────┘ └────────────┘
```

### 7.2 PostgreSQL HA (Patroni + etcd)

```yaml
# patroni.yml
scope: oeuvres_sociales
namespace: /db/
name: pg-0

restapi:
  listen: 0.0.0.0:8008
  connect_address: pg-0:8008

etcd:
  host: etcd-cluster:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 500
        shared_buffers: 4GB
        effective_cache_size: 12GB
        work_mem: 64MB
        maintenance_work_mem: 1GB
        wal_level: replica
        max_wal_senders: 5
        max_replication_slots: 5

postgresql:
  listen: 0.0.0.0:5432
  connect_address: pg-0:5432
  data_dir: /var/lib/postgresql/data
  parameters:
    archive_mode: "on"
    archive_command: pgbackrest --stanza=oeuvres archive-push %p
  pg_hba:
    - host replication replicator 0.0.0.0/0 md5
    - host all all 0.0.0.0/0 md5
```

### 7.3 RabbitMQ HA (Mirrored Queues)

```bash
# Policy pour mirroring automatique
rabbitmqctl set_policy ha-all \
  "^oeuvres\." \
  '{"ha-mode":"all","ha-sync-mode":"automatic","ha-sync-batch-size":100}' \
  --priority 1 \
  --apply-to queues
```

### 7.4 Kubernetes Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: benefits-service-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: benefits-service
```

### 7.5 Disaster Recovery

| Type | RPO | RTO | Stratégie |
|---|---|---|---|
| **AZ failure** | < 1s | < 5 min | Multi-AZ actif, Patroni auto-failover |
| **Region failure** | < 5 min | < 30 min | pgBackrest S3, restore dans region secondaire |
| **Data corruption** | < 24h | < 2h | PITR (Point-in-Time Recovery) |
| **Disaster total** | < 1h | < 4h | Warm standby dans region secondaire |

---

## 8. Sécurité Avancée

### 8.1 Zero-Trust Architecture

```
                    ┌──────────────────┐
                    │   Zero Trust     │
                    │   "Never trust,  │
                    │   always verify" │
                    └──────────────────┘
                         │        ▲
                         │        │
           ┌─────────────┼────────┼─────────────┐
           │             │        │             │
      ┌────▼────┐  ┌────▼────┐  ┌▼─────┐  ┌────▼────┐
      │  mTLS   │  │  JWT    │  │RBAC+ │  │ Service │
      │ Inter-  │  │ Short-  │  │ABAC  │  │ Mesh    │
      │ service │  │ lived   │  │      │  │(Istio)  │
      └─────────┘  └─────────┘  └──────┘  └─────────┘
```

### 8.2 mTLS entre services (Istio)

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: oeuvres-sociales
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: benefits-service-policy
spec:
  selector:
    matchLabels:
      app: benefits-service
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/oeuvres-sociales/sa/finance-service"]
      to:
        - operation:
            methods: ["GET"]
            paths: ["/api/v1/benefits/*"]
```

### 8.3 JWT avec rotation automatique

```python
# JWT Configuration avancée
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),  # Très court
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=2),    # Court
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "RS256",  # Asymétrique au lieu de HS256
    "VERIFYING_KEY": config("JWT_PUBLIC_KEY"),
    "SIGNING_KEY": config("JWT_PRIVATE_KEY"),  # Jamais partagé
    "AUDIENCE": "oeuvres-sociales-api",
    "ISSUER": "identity.oeuvres-sociales.dz",
    
    # Claims personnalisés
    "TOKEN_OBTAIN_SERIALIZER": "apps.authentication.serializers.CustomTokenObtainPairSerializer",
}
```

### 8.4 Secret Management (HashiCorp Vault)

```yaml
# vault-agent-injector annotation
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "benefits-service"
    vault.hashicorp.com/agent-inject-secret-database: "database/creds/benefits-role"
    vault.hashicorp.com/agent-inject-template-database: |
      {{- with secret "database/creds/benefits-role" -}}
      DB_PASSWORD={{ .Data.password }}
      DB_USERNAME={{ .Data.username }}
      {{- end -}}
```

### 8.5 WAF & DDoS Protection

```
┌──────────┐    ┌─────────────┐    ┌───────────┐    ┌──────────┐
│ Cloudflare│──►│ AWS WAF     │──►│ Kong      │──►│ Service  │
│  WAF      │   │  (managed)  │   │ API GW    │   │          │
├──────────┤   ├─────────────┤   ├───────────┤   ├──────────┤
│• DDoS    │   │• SQL Inj.   │   │• Rate     │   │• mTLS    │
│• Bot Mgmt│   │• XSS        │   │  Limiting │   │• RBAC    │
│• Geo Bloc│   │• CSRF       │   │• IP Bloc  │   │• Audit   │
│• Rate    │   │• API Abuse  │   │• Throttle │   │• Logging │
│  Limiting│   │• Bad Bots   │   │• Validate │   │          │
└──────────┘    └─────────────┘   └───────────┘   └──────────┘
```

**Règles WAF critiques :**

| Règle | Action | Description |
|---|---|---|
| SQLi | BLOCK | Pattern injection SQL |
| XSS | BLOCK | Script cross-site |
| Rate abuse | BLOCK (1h) | > 1000 req/5min par IP |
| Scanner | BLOCK | Détection d'outils d'attaque |
| Bad referrer | BLOCK | Requêtes sans Referer légitime |
| Large payload | BLOCK | > 10MB body |

### 8.6 Audit Trail immuable

**Audit centralisé dans Kafka :**

```python
# shared/audit/event_sourcing.py
class AuditEventProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKERS,
            value_serializer=AvroSerializer(AUDIT_SCHEMA),
            acks="all",
            compression_type="snappy",
        )
    
    def log(self, event: AuditEvent):
        # Double écriture : Kafka (source de vérité) + PostgreSQL (requêtes rapides)
        self.producer.send("audit.log", event.to_avro())
        AuditLog.objects.create(**event.to_dict())
```

---

## 9. Stratégie de Migration Progressive

### 9.1 Strangler Fig Pattern

```
Phase 1: Monolithe + Nouveaux services
┌───────────────────┐    ┌──────────┐
│   Monolith        │    │  Auth    │
│   (Django)        │    │  Service │
│                   │    │  (S1)    │
│   /api/v1/auth ◄──┤────┼──────────┤
│   /api/v1/benefits◄┼────┤ Kong GW │
└───────────────────┘    └──────────┘

Phase 2: Extraction progressive
┌───────────────────┐    ┌──────────┐    ┌──────────┐
│   Monolith        │    │  Auth    │    │ Employee │
│   (reduit)        │    │  Service │    │ Service  │
│                   │    │  (S1)    │    │  (S2)    │
│ /api/v1/benefits ◄┼────┼──────────┼────┼──────────┤
│ /api/v1/finance   │    │ Kong GW  │    │          │
└───────────────────┘    └──────────┘    └──────────┘

Phase 3: Monolithe éliminé
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Benefits │    │ Finance  │    │ Employee │    │   AI     │
│ Service  │    │ Service  │    │ Service  │    │ Service  │
│  (S3)    │    │  (S4)    │    │  (S2)    │    │  (S7)    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                      ┌──────────┐
                      │ Kong GW  │
                      └──────────┘
```

### 9.2 Order des extractions

```
Priorité 1: Auth Service (S1)
  └─ Impact minimal, zero dépendance, JWT déjà séparé
  └─ Durée: 2 semaines

Priorité 2: Employee Service (S2)
  └─ Dépend de S1 seulement, services clients stables
  └─ Durée: 3 semaines

Priorité 3: Notification Service (S8)
  └─ Déjà presque indépendant (modèles + tasks Celery)
  └─ Durée: 1 semaine

Priorité 4: Benefits Service (S3)
  └─ Coeur métier, dépend de S1, S2
  └─ Durée: 4 semaines

Priorité 5: Finance Service (S4)
  └─ Dépend de S1, S2, S3
  └─ Durée: 4 semaines

Priorité 6: Convention Service (S5)
  └─ Peu de dépendances, indépendant de S3/S4
  └─ Durée: 2 semaines

Priorité 7: Reporting Service (S6)
  └─ Lecture seule via events, pas de dépendance forte
  └─ Durée: 3 semaines

Priorité 8: AI Service (S7)
  └─ Déjà découplé via apps.get_model(), facile à extraire
  └─ Durée: 2 semaines
```

**Durée totale estimée :** 21 semaines (~5 mois)

### 9.3 Feature Flags (LaunchDarkly / Unleash)

```python
# shared/feature_flags.py
class FeatureFlags:
    flags = {
        "use_identity_microservice": False,
        "use_employee_microservice": False,
        "new_benefits_workflow": True,
        "ai_scoring_enabled": True,
        "new_dashboard_v2": False,
    }
    
    @classmethod
    def is_enabled(cls, flag: str, user=None) -> bool:
        if user and user.role == "admin":
            return True  # Admin voit toujours tout
        return cls.flags.get(flag, False)
```

### 9.4 Anti-Corruption Layer

```python
# shared/acl/benefits_adapter.py
class BenefitsAntiCorruptionLayer:
    """
    Adaptateur entre l'ancien monolithe et le nouveau Benefits microservice.
    Permet la cohabitation pendant la migration.
    """
    
    def get_benefit(self, benefit_id: str) -> dict:
        # Essayer le nouveau service d'abord
        try:
            resp = requests.get(
                f"http://benefits-svc:8000/api/v1/benefits/{benefit_id}",
                timeout=2,
            )
            if resp.status_code == 200:
                return resp.json()["data"]
        except (RequestException, ConnectionError):
            pass
        
        # Fallback vers l'ancien monolithe
        from apps.benefits.models import Benefit
        benefit = Benefit.objects.get(pk=benefit_id)
        return self._map_to_new_format(benefit)
```

---

## 10. Optimisation Performance

### 10.1 CQRS (Command Query Responsibility Segregation)

```
┌─────────────┐         ┌─────────────┐
│  Commands   │         │   Queries   │
│  (POST/PUT) │         │   (GET)     │
└──────┬──────┘         └──────┬──────┘
       │                       │
┌──────▼──────┐         ┌──────▼──────┐
│  Write DB   │         │  Read DB    │
│  (Normalized)│         │  (Denormalized)│
│  PostgreSQL │         │  PostgreSQL  │
└──────┬──────┘         │  + Redis     │
       │                │  + TimescaleDB│
       │                └─────────────┘
       │                       ▲
       └──────► Event ─────────┘
               Bus
```

**Implémentation Reporting (S6) :**

```python
# reporting/read_model.py
class DashboardReadModel:
    """Modèle de lecture dénormalisé pour le tableau de bord."""

    class Meta:
        managed = False
        db_table = "mv_dashboard_summary"

    # Champs pré-calculés depuis les événements
    total_active_employees = models.IntegerField()
    total_benefits_pending = models.IntegerField()
    total_benefits_paid_mtd = models.IntegerField()
    total_amount_paid_mtd = models.DecimalField()
    budget_consumption_pct = models.FloatField()
    conventions_expiring_30d = models.IntegerField()
    last_refreshed = models.DateTimeField()

    @classmethod
    def refresh(cls):
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_summary")
```

### 10.2 Database Indexing Strategy

```sql
-- Index composés pour les requêtes les plus fréquentes

-- Benefits: recherche par statut + date
CREATE INDEX CONCURRENTLY idx_benefits_status_date 
ON benefits_benefit (workflow_state, created_at DESC)
WHERE is_deleted = FALSE;

-- Benefits: recherche par employé
CREATE INDEX CONCURRENTLY idx_benefits_employee_date
ON benefits_benefit (employee_id, created_at DESC)
WHERE is_deleted = FALSE;

-- Payments: batch processing
CREATE INDEX CONCURRENTLY idx_payments_batch_status
ON finance_payment (batch_id, status)
WHERE is_deleted = FALSE;

-- KPI Snapshots: time-series queries
CREATE INDEX CONCURRENTLY idx_kpisnapshot_kpi_date
ON reporting_kpisnapshot (kpi_id, date DESC);

-- Full-text search employés
ALTER TABLE employees_employee ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
  to_tsvector('french', 
    coalesce(first_name, '') || ' ' || 
    coalesce(last_name, '') || ' ' || 
    coalesce(matricule, '')
  )
) STORED;
CREATE INDEX idx_employee_search ON employees_employee USING GIN (search_vector);
```

### 10.3 Connection Pooling (PgBouncer)

```yaml
# pgbouncer.ini
[databases]
oeuvres_sociales = host=pg-primary port=5432 dbname=oeuvres_sociales

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Pool sizing
pool_mode = transaction      # Transaction pooling (recommandé)
default_pool_size = 50        # Par database
max_client_conn = 500         # Total
reserve_pool_size = 10        # Pool de réserve
reserve_pool_timeout = 5      # Secondes

# Timeouts
server_idle_timeout = 600     # 10 min
client_idle_timeout = 1800    # 30 min
query_timeout = 30            # 30s max par requête
```

### 10.4 Asynchronous Task Distribution

```python
# config/celery_advanced.py
from kombu import Queue, Exchange

CELERY_TASK_QUEUES = (
    # Queues par priorité
    Queue("critical",   Exchange("critical"),   routing_key="critical"),
    Queue("default",    Exchange("default"),    routing_key="default"),
    Queue("bulk",       Exchange("bulk"),       routing_key="bulk"),
    Queue("ai",         Exchange("ai"),         routing_key="ai"),
    Queue("scheduled",  Exchange("scheduled"),  routing_key="scheduled"),
)

CELERY_TASK_ROUTES = {
    # Tâches critiques (notification paiement, workflow)
    "apps.benefits.tasks.*":             {"queue": "critical"},
    "shared.notifications.tasks.*":       {"queue": "critical"},
    
    # Tâches par défaut
    "apps.conventions.tasks.*":           {"queue": "default"},
    
    # Tâches bulk (nettoyage, purge)
    "apps.monitoring.tasks.cleanup*":     {"queue": "bulk"},
    "shared.ai.tasks.cleanup*":           {"queue": "bulk"},
    
    # Tâches AI (longues, gourmandes)
    "shared.ai.tasks.*":                  {"queue": "ai"},
    
    # Tâches planifiées
    "apps.reporting.tasks.snapshot_kpis": {"queue": "scheduled"},
    "shared.ai.tasks.run_ai_pipeline":    {"queue": "scheduled"},
}

# Concurrency workers
CELERY_WORKER_CONCURRENCY = {
    "critical": 4,   # IO-bound, beaucoup de workers
    "default": 2,
    "bulk": 1,        # 1 seul worker bulk pour éviter la surcharge
    "ai": 2,          # CPU-bound, peu de workers
    "scheduled": 1,
}
```

### 10.5 Response Compression & Serialization

```python
# DRF optimizations
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
    ),
    "COERCE_DECIMAL_TO_STRING": False,
    "UNAUTHENTICATED_USER": None,
    "NUM_PROXIES": 1,
}

# Compression middleware
MIDDLEWARE.insert(0, "django.middleware.gzip.GZipMiddleware")
```

---

## 11. Architecture Cloud-Ready

### 11.1 Kubernetes Deployment

```
oeuvres-sociales/
├── k8s/
│   ├── namespaces/
│   │   └── oeuvres-sociales.yaml
│   ├── identity-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── pdb.yaml
│   ├── benefits-service/
│   │   └── ...
│   ├── finance-service/
│   │   └── ...
│   ├── ai-service/
│   │   └── ...
│   ├── ingress/
│   │   └── kong-ingress.yaml
│   ├── rabbitmq/
│   │   └── rabbitmq-cluster.yaml
│   └── monitoring/
│       ├── prometheus.yaml
│       └── grafana.yaml
├── helm/
│   └── oeuvres-sociales/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
└── terraform/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── environments/
        ├── dev/
        ├── staging/
        └── prod/
```

### 11.2 Helm Chart (exemple)

```yaml
# helm/oeuvres-sociales/values.yaml
global:
  environment: production
  dnsZone: oeuvres-sociales.dz

identity-service:
  image:
    repository: ghcr.io/oeuvres-sociales/identity-service
    tag: latest
  replicas: 3
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1
      memory: 1Gi
  env:
    DB_HOST: pg-primary
    REDIS_URL: redis://redis-cluster:6379/0
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 6
    targetCPUUtilizationPercentage: 70

benefits-service:
  image:
    repository: ghcr.io/oeuvres-sociales/benefits-service
    tag: latest
  replicas: 4
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2
      memory: 2Gi
  env:
    DB_HOST: pg-benefits
    CELERY_BROKER_URL: amqp://guest:guest@rabbitmq:5672//
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 12

postgresql:
  patroni:
    enabled: true
    replicas: 3
  resources:
    requests:
      cpu: 2
      memory: 8Gi
    limits:
      cpu: 4
      memory: 16Gi
  storage:
    size: 100Gi
    storageClass: gp3

rabbitmq:
  replicas: 3
  resources:
    requests:
      cpu: 1
      memory: 2Gi
  persistence:
    size: 50Gi

ingress:
  kong:
    enabled: true
    replicas: 2
    annotations:
      kubernetes.io/ingress.class: kong
    tls:
      enabled: true
      secretName: oeuvres-sociales-tls
```

### 11.3 Terraform (AWS)

```hcl
# terraform/main.tf
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "oeuvres-sociales-${var.environment}"
  cidr = var.vpc_cidr
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment == "dev"
  enable_dns_hostnames   = true
}

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "oeuvres-sociales-${var.environment}"
  cluster_version = "1.30"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  node_groups = {
    main = {
      desired_capacity = 3
      min_capacity     = 3
      max_capacity     = 20
      
      instance_types = ["m6i.large", "m6i.xlarge"]
      
      k8s_labels = {
        Environment = var.environment
      }
    }
    
    ai = {
      desired_capacity = 1
      min_capacity     = 1
      max_capacity     = 4
      
      instance_types = ["g5.xlarge"]  # GPU pour ML
      
      k8s_labels = {
        Environment = var.environment
        Workload    = "ai"
      }
    }
  }
}

module "rds" {
  source = "terraform-aws-modules/rds/aws"
  
  identifier = "oeuvres-sociales-${var.environment}"
  
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.environment == "prod" ? "db.r6g.large" : "db.t3.medium"
  
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_encrypted     = true
  
  db_name  = "oeuvres_sociales"
  username = "oeuvres_admin"
  
  multi_az               = var.environment == "prod"
  backup_retention_period = 30
  backup_window          = "02:00-03:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = var.environment == "prod"
  
  vpc_security_group_ids = [module.vpc.default_security_group_id]
  db_subnet_group_name   = module.vpc.database_subnet_group
}

module "elasticache" {
  source = "terraform-aws-modules/elasticache/aws"
  
  cluster_id = "oeuvres-sociales-${var.environment}"
  
  engine         = "redis"
  engine_version = "7"
  node_type      = "cache.r6g.large"
  num_cache_nodes = var.environment == "prod" ? 3 : 1
  
  subnet_group_name = module.vpc.elasticache_subnet_group
  
  parameter_group_family = "redis7"
  
  maintenance_window = "sun:05:00-sun:06:00"
}
```

### 11.4 CI/CD Pipeline (GitLab CI)

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  REGISTRY: ghcr.io/oeuvres-sociales

# Services partagés
.shared_rules:
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG

.test_template: &test_template
  stage: test
  script:
    - pytest --cov=apps --cov=shared --cov-report=term-missing
    - ruff check .
  coverage: '/TOTAL.*\s+(\d+%)/'

Lint Django:
  stage: test
  image: python:3.12-slim
  script:
    - pip install ruff
    - ruff check --output-format=gitlab > gl-code-quality.json
  artifacts:
    reports:
      codequality: gl-code-quality.json

Test Backend:
  <<: *test_template
  services:
    - postgres:16-alpine
    - redis:7-alpine
  variables:
    DB_NAME: test_oeuvres
    DB_USER: postgres
    DB_PASSWORD: ""
    DB_HOST: postgres
    REDIS_URL: redis://redis:6379/0

Test Frontend:
  stage: test
  image: node:20-alpine
  script:
    - npm ci
    - npm run typecheck
    - npm run lint
    - npm run test -- --coverage

Build & Push:
  stage: build
  needs: [Test Backend, Test Frontend]
  script:
    - docker build -f docker/backend/Dockerfile --target production -t $REGISTRY/backend:$CI_COMMIT_SHA .
    - docker build -f docker/frontend/Dockerfile --target production -t $REGISTRY/frontend:$CI_COMMIT_SHA .
    - docker push $REGISTRY/backend:$CI_COMMIT_SHA
    - docker push $REGISTRY/frontend:$CI_COMMIT_SHA

Deploy Staging:
  stage: deploy
  environment: staging
  script:
    - helm upgrade --install oeuvres-sociales helm/oeuvres-sociales/ \
        --set global.environment=staging \
        --set identity-service.image.tag=$CI_COMMIT_SHA \
        --wait --timeout 10m
  only:
    - main

Deploy Production:
  stage: deploy
  environment: production
  script:
    - helm upgrade --install oeuvres-sociales helm/oeuvres-sociales/ \
        --set global.environment=production \
        --set identity-service.image.tag=$CI_COMMIT_SHA \
        --wait --timeout 15m
  when: manual
  only:
    - tags
```

### 11.5 Observability Stack (OpenTelemetry + Grafana)

```yaml
# docker-compose.observability.yml
version: "3.8"
services:
  prometheus:
    image: prom/prometheus:v2.50
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.3
    ports:
      - "3001:3000"
    volumes:
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true

  tempo:
    image: grafana/tempo:2.3
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./monitoring/tempo.yaml:/etc/tempo.yaml
    ports:
      - "3200:3200"  # Jaeger compatible
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP

  loki:
    image: grafana/loki:2.9
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki.yaml:/etc/loki/local-config.yaml

  opentelemetry-collector:
    image: otel/opentelemetry-collector-contrib:0.93
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./monitoring/otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"
      - "4318:4318"
    depends_on:
      - tempo
      - loki
      - prometheus
```

### 11.6 SLI / SLO / SLA

| Service | SLI | SLO | SLA |
|---|---|---|---|
| **API Gateway** | Latence p99 < 200ms | 99.9% | 99.95% |
| **Identity** | Login < 1s p95 | 99.95% | 99.99% |
| **Benefits** | CRUD < 500ms p95 | 99.9% | 99.95% |
| **Finance** | Paiement < 2s p95 | 99.9% | 99.95% |
| **AI** | Scoring < 5s p95 | 99.5% | 99.9% |
| **Notifications** | Delivery < 30s | 99.5% | 99.9% |
| **Reporting** | Dashboard < 3s p95 | 99.5% | 99.9% |

---

## 12. Roadmap & Priorisation

### Phase 0 : Foundation (Semaines 1-4)
- [ ] Kubernetes cluster + namespaces
- [ ] CI/CD pipeline (GitLab CI + Helm)
- [ ] Kong API Gateway déployée devant le monolithe
- [ ] RabbitMQ cluster + mirroring
- [ ] PostgreSQL Patroni cluster (3 nœuds)
- [ ] Redis Cluster (3 nœuds)
- [ ] Prometheus + Grafana + Loki + Tempo
- [ ] Vault + secret management
- [ ] Feature flags framework

### Phase 1 : Extraction rapide (Semaines 5-8)
- [ ] Extraction Identity Service (S1) — JWT, users, rôles
- [ ] Extraction Notification Service (S8)
- [ ] Migration Auth routes vers Kong → S1
- [ ] Mise en place mTLS entre services
- [ ] Event bus opérationnel (RabbitMQ)

### Phase 2 : Coeur métier (Semaines 9-16)
- [ ] Extraction Employee Service (S2)
- [ ] Extraction Benefits Service (S3)
- [ ] Extraction Finance Service (S4)
- [ ] Extraction Convention Service (S5)
- [ ] Sagas pour transactions multi-services
- [ ] Read replicas + cache Redis

### Phase 3 : Analytics & AI (Semaines 17-20)
- [ ] Extraction Reporting Service (S6)
- [ ] CQRS + materialized views
- [ ] Extraction AI Service (S7)
- [ ] Kafka pour event sourcing
- [ ] Feature store dédié

### Phase 4 : Optimisation (Semaines 21-24)
- [ ] Sharding PostgreSQL (partitions)
- [ ] PgBouncer connection pooling
- [ ] Cache multi-niveau (CDN + Redis + local)
- [ ] Auto-scaling HPA final
- [ ] Load testing + tuning
- [ ] Disaster Recovery drills

### Phase 5 : Advanced (Semaines 25+)
- [ ] Istio service mesh
- [ ] Multi-region active-active
- [ ] GPU workers pour ML
- [ ] Mobile app (React Native)
- [ ] Real-time WebSockets (notifications live)
- [ ] GraphQL fédéré (Apollo)

---

## Résumé des investissements

| Domaine | Effort estimé | Impact |
|---|---|---|
| **Infrastructure K8s** | 4 semaines | Base de tout le reste |
| **API Gateway** | 2 semaines | Sécurité + routage |
| **Microservices extraction** | 16 semaines | Scalabilité + indépendance |
| **Event-Driven** | 4 semaines | Découplage + résilience |
| **Base de données** | 4 semaines | Performance + HA |
| **Sécurité** | 3 semaines | Conformité + zero-trust |
| **CI/CD + Observability** | 3 semaines | DevOps + debugging |
| **Total** | **~36 semaines** | Architecture enterprise complète |

---

*Document généré le 20 Mai 2026 — Architecture Enterprise Oeuvres Sociales v1.0*
