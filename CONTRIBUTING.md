# Contributing to Oeuvres Sociales

Nous sommes ravis que vous souhaitiez contribuer ! Voici comment participer.

## Code de Conduite

Soyez respectueux, constructif et professionnel.

## Comment Contribuer

1. **Signalez un bug** → Ouvrez une issue avec les étapes de reproduction
2. **Proposez une feature** → Ouvrez une issue pour discussion
3. **Soumettez du code** → Suivez le workflow ci-dessous

## Workflow

```
develop → feature/ma-feature → MR → review → merge → develop
```

## Conventions

Voir `docs/developer/contributing.md` pour les détails complets.

TL;DR :
- **Python** : Black + isort + Ruff + mypy
- **TypeScript** : Prettier + ESLint + tsc --noEmit
- **Commits** : `feat(scope): message`

## Tests

```bash
make test       # Backend
cd frontend && npm run test  # Frontend
```

## Questions ?

Ouvrez une issue ou contactez l'équipe sur le canal #dev.
