# Dashboard variants and usage

This repo contains multiple SSA dashboard variants under `src` and `bkp`. All variants now share the same robust import logic and client-side behavior.

## Variants
- Main (production): `src/dashboard/Class/src/dashboard/ssa_dashboard.py`
  - Current standard. Uses centralized chart config, hardened clientside JS (clipboard fallback), and safe bar-chart enhancements.
  - Instantiate with a pandas DataFrame; server runs via `run_server()`.

- Backup reference: `bkp/src/dashboard/Class/src/dashboard/ssa_dashboard - Copia (3).py`
  - Canonical reference for patterns. Mirrors main behavior closely.

- Backup aligned: `bkp/src/dashboard/Class/src/dashboard/ssa_dashboard - Copia (2).py`
  - Aligned to reference; duplicates removed; typing calmers applied.

- Legacy backup updated: `bkp/src/dashboard/Class/src/dashboard/ssa_dashboard - Copia.py`
  - Legacy variant brought to parity; helpers restored; clientside copy hardened.

## Import/Path handling (backups)
- Each backup tries local relative imports first.
- If that fails, it walks up the tree to locate the repo root (by `pyproject.toml` or heuristics) and appends the repo root to `sys.path`.
- Imports then use the full package path `src.dashboard.Class.src.*` to ensure relative imports inside modules resolve correctly.

## Client-side behavior
- Clipboard copy uses `navigator.clipboard` with a fallback (textarea + execCommand) for broader browser support.
- Pattern-matching IDs are stringified for safe DOM interactions.

## Notes
- All variants successfully instantiate with a synthetic DataFrame in smoke tests.
- Week analyzer access is guarded (`getattr`) to avoid attribute errors when certain methods aren’t present.
