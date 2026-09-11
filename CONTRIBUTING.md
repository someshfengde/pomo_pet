# Contributing

Thanks for helping make Pomo Pet better. The project is intentionally small:
keep changes focused, test the surface you touched, and prefer clear behavior
over clever abstractions.

## Setup

```bash
make install
make help
```

Useful commands:

```bash
make test
make test-all
make web
npm run test:web
uv run python scripts/audit_pwa.py
```

## Repository Layout

- `src/pomo_pet/` contains the Python package for the CLI and desktop app.
- `docs/` is the static web app and GitHub Pages root. Keep it deployable as
  plain static files.
- `pets/` contains desktop pet assets.
- `docs/assets/pets/` contains bundled web pet assets.
- `tests/` covers Python and static PWA checks.
- `web-tests/` covers browser workflows with Playwright.
- `scripts/` contains repo and PWA audit utilities.

More detail lives in `docs/PROJECT_STRUCTURE.md`.

## Pull Request Checklist

- Describe the user-facing change and why it belongs in the app.
- Run `make test` for Python changes.
- Run `npm run test:web` for web UI or PWA changes.
- Run `uv run python scripts/audit_pwa.py` for static app, manifest, or service
  worker changes.
- Add or update tests when behavior changes.
- Do not commit generated files such as `.coverage`, `.DS_Store`,
  `test-results/`, `playwright-report/`, `build/`, or `dist/`.

## Adding Pets

Add desktop pets under `pets/<pet-id>/` with `pet.json` and a spritesheet. Use a
lowercase, URL-safe `id`, keep asset sizes reasonable, and include attribution
when adapting existing work. If the pet should also appear in the web app, add a
matching static asset entry under `docs/assets/pets/` and update the web pet
catalog.
