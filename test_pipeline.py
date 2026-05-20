# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Full System Test (Pipeline + Models + Risk Engine)
# Run: python test_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("IRIS — Full System Test")
print("=" * 60)

# ── Data pipeline ─────────────────────────────────────────────────────────────
print("\n[PIPELINE] Running data pipeline...")
from data.ingestion.trading_economics import fetch_all_kenya_indicators
from data.pipeline.cleaner import clean_all
from data.pipeline.merger import merge_with_historical
from data.pipeline.features import build_features

live     = fetch_all_kenya_indicators()
cleaned  = clean_all(live)
merged   = merge_with_historical(cleaned)
features = build_features(merged["combined"])
print(f"           Data ready: {len(features)} obs | {len(features.columns)} features")

# ── Model stack ───────────────────────────────────────────────────────────────
print("\n[MODELS]   Running full model stack...")
from models.model_runner import run_all_models
results = run_all_models(features)
print(f"           {results['models_ok']}/{results['models_total']} models OK | {results['elapsed_seconds']}s")

# ── Risk engine ───────────────────────────────────────────────────────────────
print("\n[RISK]     Building IRIS Risk Score...")

# Get latest readings — from live data if available, else last historical row
latest = merged.get("latest", {})
if not latest:
    last_row = features.iloc[-1]
    latest = {
        "inflation":     {"value": float(last_row["inflation"]),     "date": str(int(last_row["year"]))},
        "interest_rate": {"value": float(last_row["interest_rate"]), "date": str(int(last_row["year"]))},
    }

features_tail = features.iloc[-1].to_dict()

from risk.score_builder     import build_iris_score
from risk.regime_classifier import classify
from risk.signal_engine     import generate_signals

iris_score_result = build_iris_score(results, latest, features_tail)
classification    = classify(iris_score_result, results, latest)
signals           = generate_signals(classification, results, latest, iris_score_result)

# ── Print everything ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("IRIS RISK REPORT")
print("=" * 60)
print(f"\n  {classification['headline']}")
print(f"\n  Dominant driver : {classification['dominant_driver']}")
print(f"  Policy signal   : {classification['policy_signal']}")
print(f"  Rate action     : {signals['rate_signal']}")

print(f"\n  Component Scores:")
for k, v in iris_score_result["components"].items():
    bar = "█" * int(v / 5)
    print(f"    {k:<22} {v:>6.1f}  {bar}")

print(f"\n  Early Warnings ({len(classification['early_warnings'])}):")
for w in classification["early_warnings"]:
    print(f"    [{w['severity']:<8}] {w['flag']}")

print(f"\n  Top Signals:")
for s in signals["signals"][:4]:
    print(f"    [{s['type']:<14}] {s['action']}")

print("\n" + "=" * 60)
if results["all_models_ok"]:
    print("✅ IRIS Risk Engine operational. Ready to build the dashboard.")
print("=" * 60)