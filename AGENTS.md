# AGENTS.md

## Repository Structure

Two packages:
- **Root**: Python backend (`secure-document-vault`) — Cryptography course project.
- **`frontend/`**: Next.js 16 frontend with React 19 and TypeScript.

## Developer Commands

### Backend (root, use `uv`)
```bash
uv run flake8 .           # lint
uv run pytest             # test
uv run black .            # format (dev dependency)
uv sync --all-groups      # install all dependencies
```

CI runs: `flake8 .` → `pytest` (order matters, lint first).

### Frontend (`frontend/`)
```bash
npm run dev    # dev server
npm run build  # production build
npm run lint   # ESLint
```

No TypeScript check or test scripts defined — only ESLint.

## Python Package Architecture

- **Entry point**: `src/secure_document_vault/core/facade.py`
  - `encriptar()` — encrypt + sign a file into `.vault` format
  - `desencriptar()` — verify signature + decrypt a `.vault` file
- **Modules** (under `src/secure_document_vault/modules/`): `aead`, `key_generation`, `key_wrapping`, `randomness`, `signing`, `vault_builder`
- Tests co-located inside each module (`modules/<name>/tests/`) plus top-level `tests/`

## TypeScript Path Alias

`@/*` maps to `./src/*` (configured in `frontend/tsconfig.json`).

## Gotchas

- Code and comments are in **Spanish** (e.g., `encriptar`, `desencriptar`, `nonce_generado`).
- Python 3.12+ required (`requires-python = ">=3.12"` in `pyproject.toml`).
- Frontend uses Next.js App Router (`src/app/`).
- `.flake8` ignores E203, W503, W504 and enforces max-line-length 88 (Black default).