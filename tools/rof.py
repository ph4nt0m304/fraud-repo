#!/usr/bin/env python3
"""Interactive Return on Fraud (RoF) and sensitivity calculator.

Model (chapter 13, appendix E):

    gross   = V * p_success
    loss    = V * p_detection * p_recovery
    net     = gross - C_fixed - C_variable - loss
    capital = C_fixed + C_variable
    RoF     = net / capital

Usage:
    python3 tools/rof.py                 # interactive, French
    python3 tools/rof.py --lang en       # interactive, English
    python3 tools/rof.py --example --no-input
    python3 tools/rof.py --value 20000000 --success .7 --fixed 93000 \\
        --variable 107000 --detection .4 --recovery .25 --json

Sensitivity moves each parameter by --delta (default 10%) in the direction
that favours the operator, exactly like the table in chapter 13.3: value and
success rate up, costs and detection/recovery probabilities down.
"""

from __future__ import annotations

import argparse
import json
import sys

EXAMPLE = {
    "value": 20_000_000.0,
    "success": 0.70,
    "fixed": 93_000.0,
    "variable": 107_000.0,
    "detection": 0.40,
    "recovery": 0.25,
}

LABELS = {
    "fr": {
        "value": ("Valeur extraite (V)", "€"),
        "success": ("Taux de réussite p_success (0-1)", ""),
        "fixed": ("Coûts fixes C_fixed", "€"),
        "variable": ("Coûts variables C_variable", "€"),
        "detection": ("Probabilité de détection p_detection (0-1)", ""),
        "recovery": ("Probabilité de récupération p_recovery (0-1)", ""),
        "gross": "Produit espéré",
        "loss": "Perte espérée",
        "capital": "Capital engagé",
        "net": "Profit net espéré",
        "rof": "RoF (profit net / capital)",
        "per": "Profit net par tranche de 1 000 € engagés",
        "sens_title": "Sensibilité ±{pct} (impact sur le profit net)",
        "param": "Paramètre",
        "change": "Variation",
        "impact": "Impact",
        "share": "Part",
        "bands": [
            (0.0, "opération perdante — le coût dépasse le gain espéré"),
            (1.0, "marginal — à peine mieux que le risque zéro"),
            (3.0, "correct — rentable mais exposé"),
            (10.0, "élevé — attire les opérateurs"),
            (float("inf"), "exceptionnel — c'est ce qui rend le trade finance attractif"),
        ],
        "band": "Lecture",
        "coupling": "Le modèle complet lie V à la perte espérée (V × p_détection × p_récupération).",
        "hint": "Entrée seule = valeur par défaut entre crochets.",
        "bad_prob": "valeur attendue entre 0 et 1",
        "bad_num": "valeur numérique attendue",
        "bad_pos": "valeur strictement positive attendue",
    },
    "en": {
        "value": ("Value extracted (V)", "€"),
        "success": ("Success rate p_success (0-1)", ""),
        "fixed": ("Fixed costs C_fixed", "€"),
        "variable": ("Variable costs C_variable", "€"),
        "detection": ("Detection probability p_detection (0-1)", ""),
        "recovery": ("Recovery probability p_recovery (0-1)", ""),
        "gross": "Expected gross",
        "loss": "Expected loss",
        "capital": "Capital committed",
        "net": "Expected net profit",
        "rof": "RoF (net profit / capital)",
        "per": "Net profit per €1,000 committed",
        "sens_title": "Sensitivity ±{pct} (impact on net profit)",
        "param": "Parameter",
        "change": "Change",
        "impact": "Impact",
        "share": "Share",
        "bands": [
            (0.0, "losing operation — cost exceeds expected gain"),
            (1.0, "marginal — barely better than no risk at all"),
            (3.0, "decent — profitable but exposed"),
            (10.0, "high — attracts operators"),
            (float("inf"), "exceptional — that is why trade finance attracts"),
        ],
        "band": "Reading",
        "coupling": "The full model couples V to the expected loss (V × p_detection × p_recovery).",
        "hint": "Press Enter alone to accept the default in brackets.",
        "bad_prob": "expected a value between 0 and 1",
        "bad_num": "expected a number",
        "bad_pos": "expected a strictly positive value",
    },
}

PROBABILITIES = ("success", "detection", "recovery")
COSTS = ("fixed", "variable")


def compute(value: float, success: float, fixed: float, variable: float,
            detection: float, recovery: float) -> dict[str, float]:
    gross = value * success
    loss = value * detection * recovery
    capital = fixed + variable
    net = gross - fixed - variable - loss
    return {
        "gross": gross,
        "loss": loss,
        "capital": capital,
        "net": net,
        "rof": net / capital if capital else float("inf"),
    }


def sensitivity(values: dict[str, float], delta: float) -> list[dict[str, float | str]]:
    base = compute(**values)["net"]
    moves = {
        "value": lambda x: x * (1 + delta),
        "success": lambda x: min(1.0, x * (1 + delta)),
        "detection": lambda x: x * (1 - delta),
        "recovery": lambda x: x * (1 - delta),
        "fixed": lambda x: x * (1 - delta),
        "variable": lambda x: x * (1 - delta),
    }
    out = []
    for name, move in moves.items():
        trial = dict(values)
        trial[name] = move(values[name])
        rof = compute(**trial)["rof"]
        out.append({
            "param": name,
            "new_value": trial[name],
            "delta_net": compute(**trial)["net"] - base,
            "rof": rof,
        })
    out.sort(key=lambda row: row["delta_net"], reverse=True)
    return out


def fmt_money(amount: float) -> str:
    text = f"{amount:,.0f}".replace(",", "\u202f")
    return f"{text}\u00a0€"


def fmt_prob(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") if value % 1 else f"{value:.0f}"


def fmt_rof(value: float) -> str:
    return "∞" if value == float("inf") else f"{value:.2f}"


def read_number(prompt: str, default: float, kind: str, lang: str) -> float:
    table = LABELS[lang]
    while True:
        try:
            raw = input(f"{prompt} [{fmt_prob(default) if kind == 'prob' else f'{default:,.0f}'.replace(',', ' ')}] : ").strip()
        except EOFError:
            print()
            return default
        if not raw:
            return default
        try:
            number = float(raw.replace(" ", "").replace("\u202f", "").replace(",", "."))
        except ValueError:
            print(f"  ! {table['bad_num']}")
            continue
        if kind == "prob" and not 0.0 <= number <= 1.0:
            print(f"  ! {table['bad_prob']}")
            continue
        if kind == "money" and number < 0:
            print(f"  ! {table['bad_pos']}")
            continue
        if kind == "capital" and number <= 0:
            print(f"  ! {table['bad_pos']}")
            continue
        return number


def read_inputs(args: argparse.Namespace, lang: str) -> dict[str, float]:
    table = LABELS[lang]
    values: dict[str, float] = {}
    print(f"\n{table['hint']}\n")
    for key in EXAMPLE:
        flag = getattr(args, key, None)
        if flag is not None:
            values[key] = float(flag)
            continue
        kind = "prob" if key in PROBABILITIES else ("capital" if key in COSTS else "money")
        label = table[key][0]
        values[key] = read_number(f"{label}", EXAMPLE[key], kind, lang)
    return values


def print_report(values: dict[str, float], lang: str, delta: float) -> None:
    table = LABELS[lang]
    result = compute(**values)
    rof = result["rof"]

    print()
    for key in ("gross", "loss", "capital", "net"):
        print(f"  {table[key]:<38} {fmt_money(result[key]):>18}")
    print(f"  {table['rof']:<38} {fmt_rof(rof):>18}")

    reading = table["bands"][-1][1]
    for limit, text in table["bands"]:
        if rof < limit:
            reading = text
            break
    print(f"  {table['band']:<38} {reading}")
    if note := table.get("coupling"):
        print(f"\n  {note}")

    rows = sensitivity(values, delta)
    biggest = max((abs(row["delta_net"]) for row in rows), default=0) or 1
    print(f"\n  {table['sens_title'].format(pct=f'{delta:.0%}')}\n")
    print(f"  {table['param']:<12} {table['change']:>14} {table['impact']:>16} {table['share']:>8}")
    print(f"  {'-' * 12} {'-' * 14} {'-' * 16} {'-' * 8}")
    for row in rows:
        change = f"{row['new_value']:,.4f}".rstrip("0").rstrip(".") if row["param"] in PROBABILITIES else fmt_money(row["new_value"])
        share = abs(row["delta_net"]) / biggest
        bar = "█" * max(1, round(share * 18)) if row["delta_net"] > 0 else "·"
        print(f"  {row['param']:<12} {change:>14} {fmt_money(row['delta_net']):>16} {bar:<8}")
    print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Return on Fraud and sensitivity calculator (chapter 13 model).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--value", type=float, help="value extracted (V)")
    parser.add_argument("--success", type=float, help="success rate, 0-1")
    parser.add_argument("--fixed", type=float, help="fixed costs")
    parser.add_argument("--variable", type=float, help="variable costs")
    parser.add_argument("--detection", type=float, help="detection probability, 0-1")
    parser.add_argument("--recovery", type=float, help="recovery probability, 0-1")
    parser.add_argument("--delta", type=float, default=0.10, help="sensitivity step, e.g. 0.10 for ±10%%")
    parser.add_argument("--lang", choices=("fr", "en"), default="fr", help="output language")
    parser.add_argument("--json", action="store_true", help="machine-readable output, no prompts")
    parser.add_argument("--no-input", action="store_true", help="never prompt, use defaults for missing values")
    parser.add_argument("--example", action="store_true", help="load the €20M worked example")
    args = parser.parse_args(argv)

    for key in PROBABILITIES:
        value = getattr(args, key)
        if value is not None and not 0.0 <= value <= 1.0:
            parser.error(f"--{key} must be between 0 and 1")
    if args.value is not None and args.value <= 0:
        parser.error("--value must be strictly positive")
    for key in COSTS:
        value = getattr(args, key)
        if value is not None and value < 0:
            parser.error(f"--{key} must be zero or positive")
    if args.delta <= 0 or args.delta >= 1:
        parser.error("--delta must be between 0 and 1 (excluded)")
    if args.example:
        for key, value in EXAMPLE.items():
            if getattr(args, key) is None:
                setattr(args, key, value)
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    lang = args.lang

    missing = [key for key in EXAMPLE if getattr(args, key) is None]
    interactive = missing and not args.json and not args.no_input and sys.stdin.isatty()
    if interactive:
        values = read_inputs(args, lang)
    else:
        values = {
            key: getattr(args, key) if getattr(args, key) is not None else EXAMPLE[key]
            for key in EXAMPLE
        }

    if args.json:
        payload = {
            "inputs": values,
            "results": {k: round(v, 2) for k, v in compute(**values).items()},
            "sensitivity": [
                {**row, "new_value": round(row["new_value"], 4), "delta_net": round(row["delta_net"], 2), "rof": round(row["rof"], 4)}
                for row in sensitivity(values, args.delta)
            ],
            "delta": args.delta,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print_report(values, lang, args.delta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
