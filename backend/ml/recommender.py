import json
import os

_SCHEMES_PATH = os.path.join(os.path.dirname(__file__), "schemes.json")

def _load_schemes():
    with open(_SCHEMES_PATH, "r") as f:
        return json.load(f)


def recommend_schemes(user_data: dict, credit_score: int, risk_level: str) -> dict:
    """
    Returns:
      eligible_schemes   – list of scheme dicts with eligibility_reason
      ineligible_schemes – list of scheme dicts with rejection_reasons list
    """
    schemes = _load_schemes()

    monthly_income = float(user_data.get(
        "monthly_income_estimate",
        user_data.get("avg_daily_income", 0) * user_data.get("work_days_per_month", 26)
    ))
    occupation     = user_data.get("occupation", "")
    has_bank       = user_data.get("has_bank_account", 0)
    digital_usage  = user_data.get("digital_transaction_usage", 0)

    eligible   = []
    ineligible = []

    for scheme in schemes:
        reasons_failed = []

        # Income lower bound
        if monthly_income < scheme["min_monthly_income"]:
            reasons_failed.append(
                f"Monthly income ₹{monthly_income:.0f} is below minimum ₹{scheme['min_monthly_income']}"
            )

        # Income upper bound
        if scheme["max_monthly_income"] and monthly_income > scheme["max_monthly_income"]:
            reasons_failed.append(
                f"Monthly income ₹{monthly_income:.0f} exceeds maximum ₹{scheme['max_monthly_income']}"
            )

        # Occupation match
        if occupation not in scheme["target_occupations"]:
            reasons_failed.append(
                f"Occupation '{occupation}' not in target group for this scheme"
            )

        # Risk level
        if risk_level not in scheme["risk_levels_allowed"]:
            reasons_failed.append(
                f"Risk level '{risk_level}' not accepted (allowed: {', '.join(scheme['risk_levels_allowed'])})"
            )

        # CIBIL / bank account requirement
        if scheme["requires_cibil"] and not has_bank:
            reasons_failed.append("Requires formal bank account / CIBIL history")

        if reasons_failed:
            ineligible.append({
                "id":               scheme["id"],
                "name":             scheme["name"],
                "provider_type":    scheme["provider_type"],
                "max_amount":       scheme["max_amount"],
                "interest_rate":    scheme["interest_rate"],
                "description":      scheme["description"],
                "rejection_reasons": reasons_failed,
            })
        else:
            # Build a human-readable eligibility reason
            why = _build_eligibility_reason(scheme, monthly_income, credit_score, digital_usage)
            eligible.append({
                "id":               scheme["id"],
                "name":             scheme["name"],
                "provider_type":    scheme["provider_type"],
                "max_amount":       scheme["max_amount"],
                "interest_rate":    scheme["interest_rate"],
                "description":      scheme["description"],
                "eligibility_note": scheme["eligibility_note"],
                "eligibility_reason": why,
                "is_best_match":    False,   # set below
            })

    # Mark best match: lowest interest rate among eligible
    if eligible:
        best = min(eligible, key=lambda s: s["interest_rate"])
        best["is_best_match"] = True

    return {"eligible_schemes": eligible, "ineligible_schemes": ineligible}


def _build_eligibility_reason(scheme: dict, monthly_income: float, credit_score: int, digital_usage: float) -> str:
    parts = []
    if scheme["provider_type"] == "government":
        parts.append("Government-backed scheme")
    if not scheme["requires_cibil"]:
        parts.append("no CIBIL score required")
    if monthly_income >= scheme["min_monthly_income"]:
        parts.append(f"income meets minimum requirement")
    if credit_score >= 60:
        parts.append("good credit score")
    if digital_usage > 0.4:
        parts.append("digital transaction history available")
    return "Eligible — " + ", ".join(parts) + "."
