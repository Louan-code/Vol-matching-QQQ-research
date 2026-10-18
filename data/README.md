# Données

## Fournies dans le dépôt

- **`qqq_weekly.csv`** — QQQ hebdomadaire ajusté (splits + dividendes),
  nov. 1999 → oct. 2026. Source : Alpha Vantage `TIME_SERIES_WEEKLY_ADJUSTED`.
  Suffit pour reproduire l'étude longue (`backtest.py`, `make_outputs.py`,
  `enrichment.py`).
- **`qqq_daily_recent.csv`** — QQQ daily (~100 derniers jours). Source :
  Alpha Vantage `TIME_SERIES_DAILY` (compact).

## À fournir séparément (git-ignorées)

Volumineuses et/ou propriétaires, non commitées :

| Fichier attendu | Contenu | Utilisé par |
|---|---|---|
| `QQQ_5M.csv` | QQQ barres 5-min, 2020-2026 (`ts,open,high,low,close,volume`) | `backtest_intraday.py` |
| `options_QQQ_4h.parquet` | Options QQQ 4h (OHLCV par contrat) | `vol_signals.py` → signal IV |
| `qqq_daily_from5m.parquet` | Daily OHLC + realized variance, dérivé du 5-min | `backtest_intraday.py`, `backtest_combined.py` |

### Régénérer les dérivés

- `qqq_daily_from5m.parquet` : agrégation RTH (9h30-16h ET) des barres 5-min en
  daily OHLC + `rv_total` (realized variance intraday + gap overnight²). Voir le
  bloc de construction dans l'historique de `backtest_intraday.py`.
- Signal IV quotidien : `vol_signals.build_daily_iv(<options.parquet>)` →
  VXN-maison model-free + IV ATM + spot implicite par parité.

### Fournisseurs suggérés pour l'intraday / options
Polygon.io, Databento, Kibot. Pour la vol implicite, viser **du EOD (1 snapshot/jour)
sur plusieurs années** plutôt que de l'intraday fin : la largeur du strike et la
profondeur historique priment sur la résolution temporelle.

### Taux sans risque
Approximé constant dans les backtests (2 % hebdo / 3 % intraday). Pour plus de
précision, brancher `TREASURY_YIELD` (3M) d'Alpha Vantage.
