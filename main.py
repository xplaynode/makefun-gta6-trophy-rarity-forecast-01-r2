"""GTA VI trophy rarity forecaster: conservatively damped log-time trend.

Written for gta6-trophy-rarity-forecast-01, second entry. The program reads
every case file in the input directory and, for each trophy, writes five
quantiles of the trophy's Exophase earn rate (percent of tracked players)
at the case's target.

Model, in one paragraph: an earn rate climbs as the tracked cohort plays,
and on the logit scale that climb is close to linear in log-time since
release. For every trophy we fit a recency-weighted least-squares line of
logit(rate) against ln(1 + hours since release) over the distinct snapshots
in the history (Exophase refreshes in steps, so consecutive identical reads
are collapsed to one first). The line is anchored at the last read and its
slope is damped by 0.35 before extrapolating to the target. The heavier
damping is the point of this revision: across two independent synthetic
backtest protocols (the original 32-candidate tournament's generator,
recovered and re-run exactly, and a second generator built for this entry),
a strongly damped trend beat both the lightly damped trend and pure
persistence on every suite, continuation and denominator-surge alike,
because a 4.5-day extrapolation of a launch-week slope mostly compounds
noise, while the direction of the climb is real. The spread combines a
random-walk term (0.5 logit per sqrt-day) with the trend fit's residual
and observed refresh-jump scatter, scaled by 0.7 (the calibration both
protocols preferred); a history with almost no distinct snapshots gets a
wider band. Tier saturation caps bound the median, and no median moves
more than +/-3.5 logit from the last observed rate.

Standard library only, no network, deterministic byte for byte.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]
RELEASE = datetime(2026, 11, 19, 0, 0, 0, tzinfo=timezone.utc)

DAMP = 0.35            # slope damping for the multi-day extrapolation
SPREAD_SCALE = 0.7     # calibration on the combined spread
RW_SIGMA = 0.5         # random-walk spread, logit per sqrt-day
RESID_WEIGHT = 0.6     # weight of fit-residual scatter in the spread
FLAT_WIDEN = 1.6       # spread multiplier when history has <3 snapshots
DECAY = 0.55           # recency weight decay per distinct snapshot
LOW_RATE_BUMP = 0.1    # extra spread for trophies still under 0.5%
MIN_SPREAD = 0.2       # a band never reports less uncertainty than this


def clamp_rate(x):
    return min(99.99, max(0.01, x))


def logit(pct):
    p = clamp_rate(pct) / 100.0
    return math.log(p / (1.0 - p))


def inv_logit(value):
    if value >= 0:
        return 100.0 / (1.0 + math.exp(-value))
    e = math.exp(value)
    return 100.0 * e / (1.0 + e)


def round4(x):
    scaled = x * 10000.0
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000.0
    return int(value) if float(value).is_integer() else value


def parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def hours_since_release(moment):
    return max(0.0, (moment - RELEASE).total_seconds() / 3600.0)


def weighted_line(xs, ys, ws):
    """Weighted least squares y ~ a + b x; returns (a, b, residual sd)."""
    total_w = sum(ws)
    mean_x = sum(w * x for w, x in zip(ws, xs)) / total_w
    mean_y = sum(w * y for w, y in zip(ws, ys)) / total_w
    sxx = sum(w * (x - mean_x) ** 2 for w, x in zip(ws, xs))
    if sxx <= 1e-12:
        return mean_y, 0.0, 0.3
    sxy = sum(w * (x - mean_x) * (y - mean_y) for w, x, y in zip(ws, xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    if len(residuals) > 2:
        mu = sum(residuals) / len(residuals)
        sd = math.sqrt(sum((r - mu) ** 2 for r in residuals) / len(residuals))
    else:
        sd = 0.3
    return intercept, slope, sd


def distinct_snapshots(history):
    """Collapse consecutive reads that show the same page (no refresh between)."""
    out = []
    for read in history:
        key = (read.get("players_tracked"), tuple(read.get("rates") or []))
        if not out or out[-1][0] != key:
            out.append((key, read))
    return [read for _, read in out]


def tier_cap(tier):
    return {"platinum": 40.0, "gold": 70.0, "silver": 90.0}.get(tier, 99.5)


def forecast_trophy(index, trophy, snaps, x_target, horizon_days):
    last_rate = snaps[-1]["rates"][index]
    last_logit = logit(last_rate if last_rate is not None else 0.0)

    xs, ys, ws = [], [], []
    count = len(snaps)
    for k, read in enumerate(snaps):
        rate = read["rates"][index]
        if rate is None:
            continue
        x = math.log1p(hours_since_release(parse_time(read["at"])))
        xs.append(x)
        ys.append(logit(rate))
        ws.append(DECAY ** (count - 1 - k))

    median = last_logit
    resid_sd = 0.3
    jump_sd = 0.0
    if len(ys) >= 3:
        steps = [abs(b - a) for a, b in zip(ys, ys[1:])]
        jump_sd = sum(steps) / len(steps)
    if len(xs) >= 3 and max(xs) - min(xs) > 0.05:
        _, slope, resid_sd = weighted_line(xs, ys, ws)
        trend = last_logit + DAMP * slope * (x_target - xs[-1])
        # No extrapolation may move a median more than 3.5 logit from the
        # last observed rate, however steep the fitted slope is.
        median = last_logit + max(-3.5, min(3.5, trend - last_logit))

    # Saturation: a trophy cannot pass its tier's plausible ceiling, and a
    # forecast median never drops below a small floor.
    cap_logit = logit(tier_cap(trophy.get("tier")))
    median = min(cap_logit, max(logit(0.02), median))

    rw = RW_SIGMA * math.sqrt(horizon_days)
    # Refresh moves arrive as jumps, not smooth drift: let the observed
    # step size floor the scatter term when it exceeds the fit residual.
    scatter = max(resid_sd, 0.7 * jump_sd)
    resid = RESID_WEIGHT * scatter * math.sqrt(horizon_days)
    spread = SPREAD_SCALE * math.sqrt(rw * rw + resid * resid)
    if len(snaps) < 3:
        spread *= FLAT_WIDEN
    if last_rate is not None and last_rate < 0.5:
        spread += LOW_RATE_BUMP
    spread = max(MIN_SPREAD, spread)

    row = [round4(inv_logit(median + z * spread)) for z in Z]
    # Rounding must never break the non-decreasing order.
    for i in range(1, len(row)):
        if row[i] < row[i - 1]:
            row[i] = row[i - 1]
    return {"id": trophy["id"], "q": row}


def forecast_case(case, name):
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    if not case["history"]:
        raise ValueError(f"{name} has no history")
    # Only the recent snapshots inform the fit; the launch-night page is
    # ancient history by the final, and dropping it keeps the run fast.
    snaps = distinct_snapshots(case["history"])[-48:]
    x_target = math.log1p(hours_since_release(parse_time(case["target"])))
    horizon_days = case["horizon_minutes"] / 1440.0
    rows = [
        forecast_trophy(i, trophy, snaps, x_target, horizon_days)
        for i, trophy in enumerate(case["trophies"])
    ]
    return {"trophies": rows}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        text = json.dumps(forecast, separators=(",", ":")) + "\n"
        (OUTPUT_DIR / f"{path.stem}.out").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
