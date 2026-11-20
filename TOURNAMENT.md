# Tournament record — gta6-trophy-rarity-forecast-01, entry r2

## Why a second tournament

The first entry was selected by a 32-candidate tournament on one synthetic
protocol, where its shipped program scored, in mean pinball loss on the
logit scale: suite A (16 continuation cases) 0.3327, suite B (8 adversarial
denominator-surge cases) 0.9223, combined 0.5292 — worse than the house
persistence baseline combined (0.4214), because suite B punishes any upward
extrapolation. This revision asked whether a wider search finds an approach
that beats the incumbent program on the combined score without betting the
entry on one generator's opinion of the world.

## Protocols

Two independent synthetic generators, each producing final-like cases
(55 trophies, cut at ~60 h after release, 4.52-day horizon, Exophase-style
step refreshes freezing the page between jumps):

- **Protocol O (original):** the first build's generator and suite
  construction, recovered from its session record and re-run exactly
  (seeds 20261120 / 777). Validation: the incumbent program re-scores
  A 0.3327 / B 0.9223 / combined 0.5292 — its published backtest to four
  decimals — and the parameter replica of the incumbent inside the new
  model family reproduces the incumbent program exactly on both protocols.
- **Protocol N (new):** a second generator written for this entry —
  logit-linear accumulation in log-time with per-trophy speeds and tier
  saturation caps anchored to the real launch-night rates, logistic
  tracked-player growth, refreshes every 4–10 h, per-refresh random-walk
  jitter on the logit scale. Suites A (16 continuation), B (8 surge,
  answers diluted by a post-checkpoint factor 1.8–2.6), plus a robustness
  suite C (8 cases: faster in-history denominator growth, harder late
  saturation), reported but not gated.

Scoring is the competition's: mean pinball loss on the logit scale over
every trophy and quantile, plus 90% coverage.

## Candidates (79 evaluated)

A parameterized family spanning: persistence at several sigmas and spread
shapes; recency-weighted log-time trends with slope damping 0.3–1.0,
recency decay 0.4–1.0, fit windows 12/24/48 snapshots; earners/denominator
blends at weights 0.15–0.7 with clamps 0.6/1.2/2.0 and denominator
treatments extrapolated / frozen / half-damped; median shrinkage toward
the last rate (0.1–0.35); per-tier slope shrinkage (0.3/0.5); spread scales
0.6–1.15 and random-walk sigmas 0.35–0.65 — plus the incumbent program
itself, run as a contestant on identical cases in both protocols.

## Parity gate (declared before the refinement rounds)

A replacement is submitted only if it beats the incumbent program on the
combined (16 A + 8 B) score of **both** protocols by at least 5%, with
suite A no worse than the incumbent's by more than 2% and suite B no worse
by more than 10%, on either protocol. Anything else keeps the incumbent:
the platform counts the newest submission as the final entry, so a worse
replacement would destroy a better one.

Pure persistence (sigma 0.3) is the cautionary case: best combined score
on protocol N (0.2826 vs incumbent 0.4098) and +20% on protocol O combined
(0.4227 vs 0.5292) — but its protocol-O suite A is 0.4301 against the
incumbent's 0.3327, a 29% loss in the world where dynamics continue. It
fails the gate and was not submitted.

## Winner

**Damped trend, damping 0.35, no earners blend, spread scale 0.7** —
everything else as the incumbent (decay 0.55, 48-snapshot window,
random-walk sigma 0.5, residual weight 0.6, jump-scatter floor, 1.6x
flat-history widening, tier caps, ±3.5 logit move clamp). It is the
maximin candidate: the best worst-case combined improvement over the
incumbent across the two protocols, and it beats the incumbent on every
suite of both:

| suite | incumbent | winner | change |
|---|---|---|---|
| N-A (16 continuation) | 0.2858 | 0.2278 | −20.3% |
| N-B (8 surge) | 0.6578 | 0.5125 | −22.1% |
| N-C (8 robustness) | 0.2693 | 0.2093 | −22.3% |
| N combined | 0.4098 | 0.3227 | −21.3% |
| O-A (16 continuation) | 0.3327 | 0.3060 | −8.0% |
| O-B (8 surge) | 0.9223 | 0.5700 | −38.2% |
| O combined | 0.5292 | 0.3940 | −25.5% |

90% coverage: N-A 1.000, N-B 0.914, O-A 0.999, O-B 0.757 (incumbent O-B:
0.655 — the narrower band still covers the surge suite better than the
incumbent's wider one, because its median sits closer).

## Verification of the shipped program

main.py in this repository was imported and run over every case of both
protocols: its losses equal the tournament winner's to within 1e-9 on all
five suites. On the kit practice cases it runs in ~0.05 s per case and its
outputs are byte-identical across 3 runs (the flat launch-night histories
make its practice rows equal the incumbent's: both spreads fall under the
0.2-logit floor there).
