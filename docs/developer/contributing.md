# Contributing

## Branches

- `main` — Production (protégée)
- `develop` — Intégration continue
- `feature/*` — Nouvelles fonctionnalités
- `fix/*` — Corrections de bugs
- `release/*` — Préparation de release

## Workflow

1. Créer une branche depuis `develop`
2. Développer sur la branche
3. Ouvrir une MR/PR vers `develop`
4. Review par au moins un pair
5. Merge → CI déploie sur staging
6. Validation → Merge vers `main` → Production

## Conventions de Code

### Python (Backend)
- **Formatter** : Black (line length: 100)
- **Imports** : isort (compatible Black)
- **Linter** : Ruff (tous les codes)
- **Types** : mypy (strict mode)
- Pas de commentaires superflus
- Docstrings : Google style (uniquement pour les APIs publiques)

### TypeScript / React (Frontend)
- **Formatter** : Prettier
- **Linter** : ESLint (config React + TypeScript)
- **Types** : strict TypeScript (`tsc --noEmit`)
- Composants fonctionnels + hooks
- Pas de `any` — types explicites

### Commit Messages
```
<type>(<scope>): <sujet>

<corps optionnel>
```

Types : `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `ci`

Exemples :
```
feat(ai): add anomaly detection endpoint
fix(auth): refresh token rotation
docs(api): update endpoint documentation
```

## Pull Request Checklist

- [ ] Code formaté (black + isort + prettier)
- [ ] Lint passe (ruff + eslint)
- [ ] Typecheck passe (mypy + tsc)
- [ ] Tests passent (pytest + npm test)
- [ ] Coverage ≥ 80%
- [ ] Pas de `print` / `console.log` de debug
- [ ] Secrets dans `.env` (pas hardcodés)
- [ ] Documentation mise à jour si nécessaire

## Code Review

- Vérifier la sécurité (SQL injection, XSS, CSRF)
- Vérifier les performances (N+1, cache)
- Vérifier la gestion d'erreurs
- Vérifier les types Python/TypeScript
- Vérifier les tests
