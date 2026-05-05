"""Data source adapters for Vectaris.

Each adapter follows a common convention:
- Returns ``None`` (or raises ``AdapterUnavailable``) when the back-end is not
  configured so the service layer can fall back to stub data gracefully.
- Logs ``adapter.<name>.unavailable`` at DEBUG level when falling back so
  operators know which data source is active without flooding logs.
"""
