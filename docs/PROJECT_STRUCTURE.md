# Project Structure

Pomo Pet ships two user experiences from one repository: a static local-first
web app and a Python desktop companion.

## Runtime Surfaces

- `docs/` is the web app and GitHub Pages root. The Pages workflow deploys this
  directory directly, so keep the app runnable with a static file server.
- `src/pomo_pet/` is the Python package used by `pomo-pet` and
  `python -m pomo_pet`.
- `pomo_pet_app.py` is the PyInstaller entry point for the macOS app bundle.
- `pets/` stores desktop pet metadata and spritesheets.
- `assets/` stores desktop sound and app assets.
- `docs/assets/` stores web-only assets, screenshots, previews, and bundled
  pets.

## Development Surfaces

- `tests/` contains Python unit/integration tests plus static PWA checks.
- `web-tests/` contains Playwright browser workflow tests.
- `scripts/audit_pwa.py` checks manifest, service worker, asset, and static app
  expectations.
- `.github/workflows/` contains GitHub Pages and release automation.
- `Formula/` contains the Homebrew formula.

## Packaging Notes

The Python package uses a standard `src/` layout. Runtime code should import
from `pomo_pet`, not from `src`.

The web app intentionally remains in `docs/` because GitHub Pages deploys that
folder. Moving it requires updating `.github/workflows/pages.yml` and any local
server commands that point at `docs/`.

Generated files should stay out of version control. Common examples include
`.coverage`, `.DS_Store`, `test-results/`, `playwright-report/`, `build/`,
`dist/`, and `node_modules/`.
