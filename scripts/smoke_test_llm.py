#!/usr/bin/env python3
"""Smoke test that runs the real LLM (Phi-3 Mini via llama-cpp-python).

Use this to verify model load and inference while monitoring system
performance (e.g. with Stats on Mac). Runs several explanation generations
with synthetic price data so you can observe CPU/RAM and latency.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.config import get_settings
from src.services.explanation_service import ExplanationService


# Base price and headlines per symbol for synthetic scenarios
SYMBOL_BASE_PRICES: dict[str, tuple[Decimal, str]] = {
    "AAPL": (Decimal("250.00"), "Apple"),
    "NVDA": (Decimal("500.00"), "Nvidia"),
    "MSFT": (Decimal("400.00"), "Microsoft"),
    "AVGO": (Decimal("180.00"), "Broadcom"),
    "AMD": (Decimal("220.00"), "AMD"),
    "INTC": (Decimal("45.00"), "Intel"),
    "AMZN": (Decimal("185.00"), "Amazon"),
    "GOOG": (Decimal("175.00"), "Google"),
    "META": (Decimal("520.00"), "Meta"),
    "TSM": (Decimal("165.00"), "TSMC"),
    "MU": (Decimal("125.00"), "Micron"),
    "ASML": (Decimal("950.00"), "ASML"),
}


def build_scenarios(symbols: list[str]) -> list[tuple[str, Decimal, Decimal, list[str]]]:
    """Build (symbol, previous_price, current_price, headlines) for each symbol."""
    scenarios = []
    for i, symbol in enumerate(symbols):
        base_price, name = SYMBOL_BASE_PRICES.get(
            symbol, (Decimal("100.00"), symbol)
        )
        # Alternate +2% and -1.8% for variety
        pct = Decimal("2.0") if i % 2 == 0 else Decimal("-1.8")
        current = base_price * (1 + pct / 100)
        headlines = [
            f"{name} reports quarterly results",
            "Tech sector sees mixed trading",
        ]
        scenarios.append((symbol, base_price, current, headlines))
    return scenarios


def main() -> int:
    """Run LLM smoke test: load model and generate several explanations.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Smoke test: LLM (Phi-3 Mini / llama-cpp-python)")
    print("=" * 60)

    try:
        settings = get_settings()
    except Exception as e:
        print(f"Failed to load settings: {e}")
        return 1

    if not settings.llama_model_path:
        print("LLAMA_MODEL_PATH is not set in .env")
        print("Set it to the path of your Phi-3 Mini GGUF file and try again.")
        return 1

    print(f"Model path: {settings.llama_model_path}")
    print(f"n_ctx: {settings.llama_n_ctx}, n_gpu_layers: {settings.llama_n_gpu_layers}")
    print()

    explanation_service = ExplanationService(
        model_path=settings.llama_model_path,
        n_ctx=settings.llama_n_ctx,
        n_gpu_layers=settings.llama_n_gpu_layers,
    )

    if not explanation_service.is_available():
        print("LLM is not available (model file missing or llama-cpp-python not installed).")
        print("Install: pip install llama-cpp-python")
        print("On Mac M2: CMAKE_ARGS=\"-DGGML_METAL=on\" pip install llama-cpp-python")
        return 1

    symbols = settings.symbols_list
    scenarios = build_scenarios(symbols)
    print(f"Stocks monitored: {len(symbols)} — {', '.join(symbols)}")
    print("Generating explanations (first call loads the model; watch CPU/RAM in Stats)...")
    print()

    total_start = time.perf_counter()
    for i, (symbol, prev, curr, headlines) in enumerate(scenarios, 1):
        start = time.perf_counter()
        explanation = explanation_service.explain_from_values(
            symbol=symbol,
            previous_price=prev,
            current_price=curr,
            headlines=headlines,
        )
        elapsed = time.perf_counter() - start
        print(f"[{i}/{len(scenarios)}] {symbol} ({elapsed:.1f}s)")
        print(f"  {explanation.text[:200]}{'...' if len(explanation.text) > 200 else ''}")
        print()

    total_elapsed = time.perf_counter() - total_start
    print("=" * 60)
    print(f"Done. Total time: {total_elapsed:.1f}s for {len(scenarios)} explanations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
