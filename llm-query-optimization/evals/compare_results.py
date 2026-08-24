import json
from pathlib import Path


# ================================================================
# Configuration
# ================================================================

BASELINE_FILE = Path("results/baseline.json")
OPTIMIZED_FILE = Path("results/optimized_benchmark.json")


# ================================================================
# Load JSON
# ================================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ================================================================
# Normalize baseline
# ================================================================

def normalize_baseline(data):
    summary = data.get("summary", {})

    latency = summary.get(
        "latency_seconds",
        {},
    )

    return {
        "questions": summary.get(
            "questions",
            0,
        ),
        "evaluated_questions": summary.get(
            "evaluated_questions",
            0,
        ),
        "correct_answers": summary.get(
            "correct_answers",
            0,
        ),
        "accuracy": summary.get(
            "accuracy_percent",
            0.0,
        ),
        "average_latency": latency.get(
            "average",
            0.0,
        ),
        "p50_latency": latency.get(
            "p50",
            0.0,
        ),
        "p95_latency": latency.get(
            "p95",
            0.0,
        ),
        "llm_calls": None,
        "total_tokens": None,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_llm_cost_usd": None,
    }


# ================================================================
# Normalize optimized
# ================================================================

def normalize_optimized(data):
    summary = data.get("summary", {})

    return {
        "questions": summary.get(
            "questions",
            0,
        ),
        "evaluated_questions": summary.get(
            "evaluated_questions",
            0,
        ),
        "correct_answers": summary.get(
            "correct_answers",
            0,
        ),
        "accuracy": summary.get(
            "accuracy",
            0.0,
        ),
        "average_latency": summary.get(
            "average_latency",
            0.0,
        ),
        "p50_latency": summary.get(
            "p50_latency",
            0.0,
        ),
        "p95_latency": summary.get(
            "p95_latency",
            0.0,
        ),
        "llm_calls": summary.get(
            "llm_calls",
            0,
        ),
        "total_tokens": summary.get(
            "total_tokens",
            0,
        ),
        "prompt_tokens": summary.get(
            "prompt_tokens",
            0,
        ),
        "completion_tokens": summary.get(
            "completion_tokens",
            0,
        ),
        "total_llm_cost_usd": summary.get(
            "total_llm_cost_usd",
            0.0,
        ),
    }


# ================================================================
# Formatting helpers
# ================================================================

def format_value(value, suffix=""):
    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.4f}{suffix}"

    return f"{value}{suffix}"


def format_percent(value):
    if value is None:
        return "N/A"

    return f"{value:.2f}%"


def format_seconds(value):
    if value is None:
        return "N/A"

    return f"{value:.4f}s"


def format_integer(value):
    if value is None:
        return "N/A"

    return f"{value:,}"


# ================================================================
# Percentage-point improvement
# ================================================================

def percentage_point_change(
    baseline,
    optimized,
):
    return optimized - baseline


# ================================================================
# Latency improvement
# ================================================================

def latency_improvement(
    baseline,
    optimized,
):
    if baseline is None or optimized is None:
        return None

    if baseline == 0:
        return None

    return (
        (baseline - optimized)
        / baseline
    ) * 100


# ================================================================
# Main
# ================================================================

def main():

    if not BASELINE_FILE.exists():
        raise FileNotFoundError(
            f"Baseline results not found: "
            f"{BASELINE_FILE}"
        )

    if not OPTIMIZED_FILE.exists():
        raise FileNotFoundError(
            f"Optimized results not found: "
            f"{OPTIMIZED_FILE}"
        )

    baseline_raw = load_json(
        BASELINE_FILE
    )

    optimized_raw = load_json(
        OPTIMIZED_FILE
    )

    baseline = normalize_baseline(
        baseline_raw
    )

    optimized = normalize_optimized(
        optimized_raw
    )

    # ============================================================
    # Header
    # ============================================================

    print()
    print("=" * 70)
    print("BASELINE vs OPTIMIZED")
    print("=" * 70)
    print()

    print(
        f"{'Metric':<35}"
        f"{'Baseline':>15}"
        f"{'Optimized':>15}"
    )

    print("-" * 65)

    # ============================================================
    # Accuracy
    # ============================================================

    print(
        f"{'Accuracy':<35}"
        f"{format_percent(baseline['accuracy']):>15}"
        f"{format_percent(optimized['accuracy']):>15}"
    )

    # ============================================================
    # Average latency
    # ============================================================

    print(
        f"{'Average latency':<35}"
        f"{format_seconds(baseline['average_latency']):>15}"
        f"{format_seconds(optimized['average_latency']):>15}"
    )

    # ============================================================
    # P50 latency
    # ============================================================

    print(
        f"{'P50 latency':<35}"
        f"{format_seconds(baseline['p50_latency']):>15}"
        f"{format_seconds(optimized['p50_latency']):>15}"
    )

    # ============================================================
    # P95 latency
    # ============================================================

    print(
        f"{'P95 latency':<35}"
        f"{format_seconds(baseline['p95_latency']):>15}"
        f"{format_seconds(optimized['p95_latency']):>15}"
    )

    # ============================================================
    # LLM calls
    # ============================================================

    print(
        f"{'LLM calls':<35}"
        f"{format_value(baseline['llm_calls']):>15}"
        f"{format_value(optimized['llm_calls']):>15}"
    )

    # ============================================================
    # Tokens
    # ============================================================

    print(
        f"{'Prompt tokens':<35}"
        f"{format_integer(baseline['prompt_tokens']):>15}"
        f"{format_integer(optimized['prompt_tokens']):>15}"
    )

    print(
        f"{'Completion tokens':<35}"
        f"{format_integer(baseline['completion_tokens']):>15}"
        f"{format_integer(optimized['completion_tokens']):>15}"
    )

    print(
        f"{'Total tokens':<35}"
        f"{format_integer(baseline['total_tokens']):>15}"
        f"{format_integer(optimized['total_tokens']):>15}"
    )

    # ============================================================
    # Cost
    # ============================================================

    baseline_cost = baseline[
        "total_llm_cost_usd"
    ]

    optimized_cost = optimized[
        "total_llm_cost_usd"
    ]

    print(
        f"{'Total LLM cost':<35}"
        f"{'N/A' if baseline_cost is None else f'${baseline_cost:.8f}':>15}"
        f"{'N/A' if optimized_cost is None else f'${optimized_cost:.8f}':>15}"
    )

    # ============================================================
    # Improvements
    # ============================================================

    print()
    print("=" * 70)
    print("IMPROVEMENTS")
    print("=" * 70)

    accuracy_change = percentage_point_change(
        baseline["accuracy"],
        optimized["accuracy"],
    )

    print(
        f"Accuracy improvement: "
        f"{accuracy_change:+.2f} percentage points"
    )

    avg_latency_change = latency_improvement(
        baseline["average_latency"],
        optimized["average_latency"],
    )

    if avg_latency_change is not None:
        print(
            f"Average latency improvement: "
            f"{avg_latency_change:+.2f}%"
        )

    p95_latency_change = latency_improvement(
        baseline["p95_latency"],
        optimized["p95_latency"],
    )

    if p95_latency_change is not None:
        print(
            f"P95 latency improvement: "
            f"{p95_latency_change:+.2f}%"
        )

    # ============================================================
    # Token reduction
    # ============================================================

    if (
        baseline["total_tokens"] is not None
        and optimized["total_tokens"] is not None
    ):
        if baseline["total_tokens"] > 0:

            token_change = (
                (
                    baseline["total_tokens"]
                    - optimized["total_tokens"]
                )
                / baseline["total_tokens"]
            ) * 100

            print(
                f"Token change: "
                f"{token_change:+.2f}%"
            )

    # ============================================================
    # Optimization result
    # ============================================================

    print()
    print("=" * 70)
    print("OPTIMIZATION RESULT")
    print("=" * 70)

    print(
        f"Questions evaluated: "
        f"{optimized['evaluated_questions']}"
    )

    print(
        f"Correct answers: "
        f"{optimized['correct_answers']}"
    )

    print(
        f"Optimized LLM calls: "
        f"{optimized['llm_calls']}"
    )

    print(
        f"Optimized total tokens: "
        f"{optimized['total_tokens']}"
    )

    print(
        f"Optimized accuracy: "
        f"{optimized['accuracy']:.2f}%"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()