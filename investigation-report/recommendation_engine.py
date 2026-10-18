
"""
EcoSpillGuard - Historical Spill Recommendation Engine

Reads historical spill cases from oil_spill_case_library_15.csv.
Finds relevant cases and returns evidence-linked recommendations.
"""

import csv
import re
from pathlib import Path


# Locate the repository and CSV relative to this script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = PROJECT_ROOT / "backend" / "oil_spill_case_library_15.csv"


def normalize(value):
    """Convert text to lowercase and remove extra whitespace."""
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def load_cases():
    """Load historical cases from the CSV file."""
    if not CASE_FILE.exists():
        raise FileNotFoundError(
            f"Historical case library not found: {CASE_FILE}"
        )

    with CASE_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {
            "case_id",
            "incident_name",
            "cause_category",
            "oil_type",
            "spill_quantity",
            "measures_taken",
            "preventive_measures",
            "source",
        }

        available = set(reader.fieldnames or [])
        missing = required - available

        if missing:
            raise ValueError(
                "CSV is missing required columns: "
                + ", ".join(sorted(missing))
            )

        cases = list(reader)

    if not cases:
        raise ValueError("The historical case library contains no cases.")

    return cases


def score_case(case, cause="", oil_type="", incident_description=""):
    """
    Rank cases using simple text matching.
    This is retrieval, not a trained machine-learning model.
    """
    score = 0
    case_cause = normalize(case.get("cause_category"))
    case_oil = normalize(case.get("oil_type"))
    description = normalize(incident_description)

    requested_cause = normalize(cause)
    requested_oil = normalize(oil_type)

    if requested_cause and requested_cause in case_cause:
        score += 5

    if requested_oil and requested_oil in case_oil:
        score += 3

    # Add a small score for meaningful words shared with the description.
    stop_words = {
        "the", "and", "for", "with", "from", "that", "this",
        "into", "was", "were", "are", "oil", "spill",
    }
    description_words = {
        word for word in re.findall(r"[a-z0-9]+", description)
        if len(word) > 3 and word not in stop_words
    }

    case_text = normalize(
        " ".join([
            case.get("incident_name", ""),
            case.get("cause_category", ""),
            case.get("oil_type", ""),
            case.get("measures_taken", ""),
            case.get("preventive_measures", ""),
        ])
    )
    case_words = set(re.findall(r"[a-z0-9]+", case_text))

    score += min(len(description_words & case_words), 5)

    return score


def recommend(
    cause="",
    oil_type="",
    incident_description="",
    top_k=3,
):
    """Return relevant cases and their evidence-linked lessons."""
    cases = load_cases()

    ranked = sorted(
        cases,
        key=lambda case: score_case(
            case,
            cause=cause,
            oil_type=oil_type,
            incident_description=incident_description,
        ),
        reverse=True,
    )

    # Avoid presenting unrelated cases as strong matches.
    results = []
    for case in ranked:
        score = score_case(
            case,
            cause=cause,
            oil_type=oil_type,
            incident_description=incident_description,
        )

        if score <= 0:
            continue

        results.append({
            "case_id": case.get("case_id", "Unknown"),
            "incident_name": case.get("incident_name", "Unknown"),
            "cause_category": case.get("cause_category", "Unknown"),
            "oil_type": case.get("oil_type", "Unknown"),
            "measures_taken": case.get("measures_taken", ""),
            "preventive_measures": case.get("preventive_measures", ""),
            "source": case.get("source", ""),
            "source_type": case.get("source_type", "Not specified"),
            "match_score": score,
            "review_note": (
                "Historical case for review; verify applicability "
                "to the current incident."
            ),
        })

        if len(results) >= max(1, top_k):
            break

    return {
        "method": "Historical case retrieval with text matching",
        "model_trained": False,
        "matched_case_count": len(results),
        "recommendations": results,
        "disclaimer": (
            "Suggestions are based on historical cases, not confirmed "
            "causes or guaranteed treatment outcomes. A qualified "
            "person must verify suitability before any response action."
        ),
    }


def main():
    print("EcoSpillGuard Historical Recommendation Engine")
    print("-" * 48)

    cases = load_cases()
    print(f"Historical cases loaded: {len(cases)}")
    print(f"CSV file: {CASE_FILE}")

    # Sample test. Change these values to test other incident types.
    results = recommend(
        cause="bunkering",
        oil_type="heavy fuel oil",
        incident_description="Possible leak during fuel transfer",
        top_k=3,
    )

    print("\nMethod:", results["method"])
    print("Model trained:", results["model_trained"])
    print("\nRelevant historical cases:")

    if not results["recommendations"]:
        print("No sufficiently relevant cases found.")
    else:
        for item in results["recommendations"]:
            print(f"\n{item['case_id']} — {item['incident_name']}")
            print("Cause category:", item["cause_category"])
            print("Measures taken:", item["measures_taken"])
            print("Preventive measures:", item["preventive_measures"])
            print("Source:", item["source"])
            print("Match score:", item["match_score"])

    print("\nImportant:", results["disclaimer"])


if __name__ == "__main__":
    main()
