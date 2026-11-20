# Vice City Forecaster r2 — GTA VI trophy rarity, week one

![make.fun](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)
![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/xplaynode/makefun-gta6-trophy-rarity-forecast-01-r2/rank.svg)
![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/xplaynode/makefun-gta6-trophy-rarity-forecast-01-r2/reward.svg)

Second entry for [gta6-trophy-rarity-forecast-01](https://make.fun/bounty/gta6-trophy-rarity-forecast-01) on make.fun: forecast, for every PlayStation 5 trophy of Grand Theft Auto VI, the percent of Exophase-tracked players who will have earned it at the target — five quantiles (5%, 25%, 50%, 75%, 95%) per trophy, produced by `python3 main.py` from the case history alone (Python 3.13, standard library only, no network, deterministic).

## What changed from the first entry

The first entry ("Vice City Forecaster") extrapolated a recency-weighted log-time trend with slope damping 0.8, blended with an earners/denominator decomposition at weight 0.25, and a spread scaled by 0.85. This revision keeps the same machinery — distinct-snapshot collapsing, recency-weighted least squares of logit(rate) against ln(1 + hours since release), anchoring at the last read, tier saturation caps, a ±3.5 logit move clamp, and a spread built from a random-walk term plus fit-residual and refresh-jump scatter — with three changes chosen by a wider tournament (see TOURNAMENT.md):

1. **Slope damping 0.35 instead of 0.8.** A launch-week slope extrapolated over 4.5 days mostly compounds noise; the direction of the climb is real, its steepness is not.
2. **The earners/denominator blend is removed.** Across both backtest protocols its pull was as likely to chase refresh noise as to catch dilution; the damped trend alone was better on every suite.
3. **Spread scale 0.7 instead of 0.85.** The incumbent's band was honestly wide but paid for it at every trophy; 0.7 was the calibration both protocols preferred, with 90% coverage staying at or above the incumbent's on the surge suite of the regenerated protocol.

## How the approach was selected

A 79-approach tournament was scored on two independent synthetic backtest protocols: the original tournament's generator (recovered from the first build's session record and re-run exactly — it reproduces the first entry's published backtest to four decimals) and a second generator written for this entry (step refreshes every 4–10 h, per-refresh random-walk jitter, logistic player growth). Each protocol has a continuation suite (16 cases) and an adversarial denominator-surge suite (8 cases). The winner had to beat the incumbent program, run on identical cases, on the combined score of **both** protocols with per-suite guards — pure persistence, the strongest candidate on the second protocol alone, was rejected because it lost the continuation suite of the first protocol by ~29%. The shipped program beat the incumbent on every suite of both protocols (combined: −21% and −26% mean pinball loss). Full record in TOURNAMENT.md.

## Running it

```
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `*.in` case file in the input directory (or `$MAKEFUN_INPUT_DIR`, else `/input`) and writes one `<id>.out` per case to the output directory (or `$MAKEFUN_OUTPUT_DIR`, else `/output`).
