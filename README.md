# AutoBetBot

Production-minded, Windows-first Python paper-trading bot scaffold for Polymarket favorite-momentum strategy across:
- BTC 5m / 15m
- ETH 5m / 15m
- SOL 5m / 15m

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

## Default paper-mode settings

- `MODE=paper`
- `ENTRY_MID_MIN=0.85`
- `ENTRY_ASK_MAX=0.86`
- `MAX_SPREAD=0.02`
- `TP_PRICE=0.95`
- `SL_PRICE=0.75`
- `TIME_STOP_SECONDS=20`
- `MAX_OPEN_POSITIONS_GLOBAL=4`
- `MAX_CAPITAL_DEPLOYED_FRACTION=0.4`
- `BTC_SIZE_MULTIPLIER=0.5`
- `ETH_SIZE_MULTIPLIER=1.0`
- `SOL_SIZE_MULTIPLIER=1.0`
- `PAPER_FILL_MODEL=conservative`

## Tests

```bash
pytest -q
```

## Notes

- Live execution is scaffolded but intentionally not implemented in v1.
- Market data connector currently uses a polling stub for paper-mode simulation if no direct CLOB wiring is provided.
