
"""Historical spill case retrieval using selective text matching, not trained ML."""

import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_FILE = PROJECT_ROOT / "backend" / "oil_spill_case_library_15.csv"

# Generic words that do not provide useful evidence of a matching spill.
STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into",
    "was", "were", "are", "has", "had", "have", "been", "being",
    "oil", "spill", "incident", "event", "sensor", "alert",
    "triggered", "investigation", "required", "suspected",
    "detected", "detection", "monitor", "monitoring", "status",
    "unknown", "unconfirmed", "unavailable", "none", "other",
}


def normalize(value):
    """Normalize text for matching."""
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def meaningful_words(value):
    """Extract meaningful words, excluding generic incident terminology."""
    return {
        word
        for word in re.findall(r"[a-z0-9]+", normalize(value))
        if len(word) > 3 and word not in STOP_WORDS
    }


def load_cases():
    if not CASE_FILE.exists():
        raise FileNotFoundError(
            f"Historical case library not found: {CASE_FILE}. "
            "Place oil_spill_case_library_15.csv in the project's backend folder."
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

        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Historical case CSV is missing columns: "
                + ", ".join(sorted(missing))
            )

        cases = list(reader)

    if not cases:
        raise ValueError("The historical case library contains no cases.")

    return cases


def score_case(case, cause="", oil_type="", incident_description=""):
    """
    Score a historical case using explicit cause, oil type,
    and meaningful overlap with the incident name/cause.

    Treatment and prevention text is deliberately excluded from matching.
    """
    score = 0

    normalized_cause = normalize(cause)
    normalized_oil = normalize(oil_type)

    case_cause = normalize(case.get("cause_category"))
    case_oil = normalize(case.get("oil_type"))

    # Explicit cause matches receive the strongest weight.
    if (
        normalized_cause
        and normalized_cause not in STOP_WORDS
        and (
            normalized_cause == case_cause
            or normalized_cause in case_cause
        )
    ):
        score += 5

    # Explicit oil-type matches provide additional evidence.
    if (
        normalized_oil
        and normalized_oil not in STOP_WORDS
        and (
            normalized_oil == case_oil
            or normalized_oil in case_oil
        )
    ):
        score += 3

    # Match only against the case identity and cause, not its advice.
    description_words = meaningful_words(incident_description)
    case_words = meaningful_words(
        " ".join(
            str(case.get(field, ""))
            for field in (
                "incident_name",
                "cause_category",
                "oil_type",
            )
        )
    )

    overlap = description_words & case_words

    # Require at least two meaningful shared terms before awarding
    # description-based points. One coincidental word is not a match.
    if len(overlap) >= 2:
        score += min(len(overlap), 3)

    return score


def recommend(cause="", oil_type="", incident_description="", top_k=3):
    cases = load_cases()

    ranked = sorted(
        (
            (case, score_case(case, cause, oil_type, incident_description))
            for case in cases
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    results = []

    for case, score in ranked:
        # Require meaningful evidence. Do not fill the list with weak matches.
        if score < 2:
            continue

        results.append(
            {
                "case_id": case.get("case_id", "Unknown"),
                "incident_name": case.get("incident_name", "Unknown"),
                "cause_category": case.get("cause_category", "Unknown"),
                "oil_type": case.get("oil_type", ""),
                "spill_quantity": case.get("spill_quantity", ""),
                "measures_taken": case.get("measures_taken", ""),
                "preventive_measures": case.get("preventive_measures", ""),
                "source": case.get("source", ""),
                "source_type": case.get("source_type", "Not specified"),
                "match_score": score,
                "review_note": (
                    "Historical case for review. Similarity does not establish "
                    "the current incident's cause or prove that these measures "
                    "are suitable."
                ),
            }
        )

        if len(results) >= max(1, top_k):
            break

    return {
        "method": "Selective historical case retrieval with text matching",
        "model_trained": False,
        "matched_case_count": len(results),
        "recommendations": results,
        "disclaimer": (
            "Suggestions are based on historical cases, not confirmed causes "
            "or guaranteed treatment outcomes. Qualified crew must verify "
            "suitability before any action."
        ),
        "message": (
            "Historical matches found."
            if results
            else (
                "Insufficient incident information for relevant historical "
                "recommendations. Record the spill cause, oil type, or more "
                "specific incident details before requesting recommendations."
            )
        ),
    }
