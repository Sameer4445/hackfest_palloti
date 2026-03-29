"""
Smart Loan Recommendation Engine
- Eligibility scoring (0-100) per scheme
- Global income-based loan cap
- EMI calculation with multiple tenures + affordability check
- Three tiers: Eligible (>=70), Partial (40-69), Rejected (<40)
"""
import json, os, math

_SCHEMES_PATH = os.path.join(os.path.dirname(__file__), "schemes.json")
_RISK_MULTIPLIER = {"Low": 11, "Medium": 7, "High": 3}
_ELIGIBLE = 70
_PARTIAL  = 40
_TENURES  = [12, 24, 36]          # months


def _load_schemes():
    with open(_SCHEMES_PATH) as f:
        return json.load(f)


# ── EMI helpers ───────────────────────────────────────────────────────────────

def calc_emi(principal: float, annual_rate: float, months: int) -> dict:
    """Standard reducing-balance EMI formula."""
    if annual_rate == 0:
        emi = principal / months
    else:
        r = annual_rate / 100 / 12
        emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total_payment  = round(emi * months, 2)
    total_interest = round(total_payment - principal, 2)
    return {
        "tenure_months":  months,
        "emi":            round(emi, 2),
        "total_payment":  total_payment,
        "total_interest": total_interest,
    }


def build_emi_options(principal: float, annual_rate: float, safe_emi_limit: float) -> dict:
    """Generate EMI plans for all tenures and pick the recommended one."""
    options = []
    for t in _TENURES:
        plan = calc_emi(principal, annual_rate, t)
        emi  = plan["emi"]
        if emi <= safe_emi_limit:
            plan["affordability"] = "safe"
            plan["affordability_label"] = "Safe"
        elif emi <= safe_emi_limit * 1.4:
            plan["affordability"] = "moderate"
            plan["affordability_label"] = "Risky"
        else:
            plan["affordability"] = "risky"
            plan["affordability_label"] = "Not Affordable"
        plan["is_recommended"] = False
        options.append(plan)

    # Recommend: longest tenure that is "safe", else shortest overall
    safe_plans = [p for p in options if p["affordability"] == "safe"]
    if safe_plans:
        safe_plans[-1]["is_recommended"] = True   # longest safe tenure
    else:
        options[0]["is_recommended"] = True        # shortest (least total interest)

    recommended = next(p for p in options if p["is_recommended"])
    return {"emi_options": options, "recommended_plan": recommended}


# ── public entry point ────────────────────────────────────────────────────────

def run_recommendation_engine(user_data: dict, credit_score: int, risk_level: str) -> dict:
    schemes = _load_schemes()

    # ── Standardize to MONTHLY units (always use * 30, never work_days) ───────
    avg_daily_income = float(user_data.get("avg_daily_income", 0))
    daily_expense    = float(user_data.get("daily_expense", 0))
    monthly_income   = round(avg_daily_income * 30, 2)
    monthly_expense  = round(daily_expense * 30, 2)

    occupation    = user_data.get("occupation", "")
    has_bank      = int(user_data.get("has_bank_account", 0))
    digital_usage = float(user_data.get("digital_transaction_usage", 0))
    expense_ratio = float(user_data.get("expense_ratio", monthly_expense / monthly_income if monthly_income else 0.7))
    savings_ratio = float(user_data.get("savings_ratio", 0.1))

    # ── Core financial calculations ───────────────────────────────────────────
    disposable_income = round(monthly_income - monthly_expense, 2)
    safe_emi_limit    = round(max(disposable_income, 0) * 0.50, 2)   # 50% of disposable
    max_loan_allowed  = round(safe_emi_limit * 20)                    # ~20 months capacity

    # ── Financial status gate ─────────────────────────────────────────────────
    if monthly_income == 0:
        fin_status  = "no_income"
        warning_msg = "No income detected — loan applications cannot be processed."
    elif monthly_income < 3000:
        fin_status  = "low_income"
        warning_msg = f"Monthly income ₹{monthly_income:,.0f} is below the minimum ₹3,000 required for any loan."
    elif disposable_income <= 0:
        fin_status  = "no_disposable"
        warning_msg = "No disposable income available. All income is consumed by expenses — taking a loan is not advisable."
    elif disposable_income < 2000:
        fin_status  = "unsafe"
        warning_msg = f"Disposable income is only ₹{disposable_income:,.0f}/mo — too low to safely service any loan EMI."
    else:
        fin_status  = "ok"
        warning_msg = None

    results = []
    for scheme in schemes:
        scored = _score_scheme(
            scheme, monthly_income, occupation, risk_level,
            has_bank, digital_usage, expense_ratio, savings_ratio,
            credit_score, max_loan_allowed, safe_emi_limit,
            disposable_income, fin_status
        )
        results.append(scored)

    results.sort(key=lambda x: x["eligibility_score"], reverse=True)

    # If financially unsafe, push everything to rejected
    if fin_status in ("no_income", "low_income", "no_disposable", "unsafe"):
        eligible = []
        partial  = []
        rejected = results
    else:
        eligible = [r for r in results if r["eligibility_score"] >= _ELIGIBLE]
        partial  = [r for r in results if _PARTIAL <= r["eligibility_score"] < _ELIGIBLE]
        rejected = [r for r in results if r["eligibility_score"] < _PARTIAL]

    if eligible:
        eligible[0]["is_best_match"] = True

    rec_amounts  = [r["recommended_amount"] for r in eligible if r["recommended_amount"] > 0]
    amount_range = {
        "min": min(rec_amounts) if rec_amounts else 0,
        "max": max(rec_amounts) if rec_amounts else 0,
    }

    return {
        "top_schemes":              eligible[:3],
        "partial_schemes":          partial,
        "rejected_schemes":         rejected,
        "recommended_amount_range": amount_range,
        "monthly_income":           monthly_income,
        "monthly_expense":          monthly_expense,
        "disposable_income":        disposable_income,
        "safe_emi_limit":           safe_emi_limit,
        "max_loan_allowed":         max_loan_allowed,
        "financial_status":         fin_status,
        "warning_message":          warning_msg,
    }


# ── scoring logic ─────────────────────────────────────────────────────────────

def _score_scheme(
    scheme: dict,
    monthly_income: float,
    occupation: str,
    risk_level: str,
    has_bank: int,
    digital_usage: float,
    expense_ratio: float,
    savings_ratio: float,
    credit_score: int,
    max_loan_allowed: float,
    safe_emi_limit: float,
    disposable_income: float,
    fin_status: str,
) -> dict:

    score        = 0
    eligible_reasons     = []
    rejection_reasons    = []
    improvement_suggestions = []

    # ── 1. Income eligibility (30 pts) ───────────────────────────────────────
    min_inc = scheme["min_monthly_income"]
    max_inc = scheme.get("max_monthly_income")

    if monthly_income >= min_inc:
        if max_inc is None or monthly_income <= max_inc:
            score += 30
            eligible_reasons.append(f"Income ₹{monthly_income:,.0f}/mo meets requirement")
        else:
            # Over income cap — partial credit
            score += 10
            rejection_reasons.append(f"Income ₹{monthly_income:,.0f} exceeds scheme cap ₹{max_inc:,}")
            improvement_suggestions.append("This scheme targets lower-income applicants; consider NBFC or bank products")
    else:
        gap = min_inc - monthly_income
        score += 0
        rejection_reasons.append(f"Income ₹{monthly_income:,.0f} below minimum ₹{min_inc:,} (gap: ₹{gap:,.0f})")
        improvement_suggestions.append(f"Increase monthly income by ₹{gap:,.0f} to qualify")

    # ── 2. Occupation match (25 pts) ─────────────────────────────────────────
    if occupation in scheme["target_occupations"]:
        score += 25
        eligible_reasons.append(f"'{occupation}' is a target occupation")
    else:
        score += 0
        rejection_reasons.append(f"Occupation '{occupation}' not in scheme's target group")
        improvement_suggestions.append("Look for schemes that cover your occupation category")

    # ── 3. Risk compatibility (25 pts) ───────────────────────────────────────
    if risk_level in scheme["risk_levels_allowed"]:
        score += 25
        eligible_reasons.append(f"{risk_level} risk profile accepted")
    else:
        score += 0
        rejection_reasons.append(f"Risk level '{risk_level}' not accepted (needs: {', '.join(scheme['risk_levels_allowed'])})")
        improvement_suggestions.append("Improve credit score and reduce expenses to lower your risk level")

    # ── 4. Financial behaviour (20 pts) ──────────────────────────────────────
    behaviour_score = 0

    # Digital usage (8 pts)
    if digital_usage >= 0.6:
        behaviour_score += 8
        eligible_reasons.append("Strong digital transaction history")
    elif digital_usage >= 0.3:
        behaviour_score += 4
    else:
        improvement_suggestions.append("Use UPI/digital payments more to build transaction history")

    # Savings ratio (7 pts)
    if savings_ratio >= 0.15:
        behaviour_score += 7
        eligible_reasons.append("Healthy savings ratio")
    elif savings_ratio >= 0.05:
        behaviour_score += 3
    else:
        improvement_suggestions.append("Try to save at least 10% of monthly income")

    # Bank account (5 pts)
    if has_bank:
        behaviour_score += 5
        eligible_reasons.append("Has formal bank account")
    else:
        if scheme.get("requires_cibil"):
            rejection_reasons.append("Requires formal bank account / CIBIL history")
            improvement_suggestions.append("Open a bank account to access more loan products")
        else:
            improvement_suggestions.append("Opening a bank account will improve eligibility for more schemes")

    score += behaviour_score

    # ── 5. Global loan cap check ──────────────────────────────────────────────
    # If scheme max_amount > max_loan_allowed, cap the recommended amount
    # but don't penalise the score — just adjust the amount
    recommended_amount = int(min(scheme["max_amount"], max_loan_allowed))

    if scheme["max_amount"] > max_loan_allowed:
        eligible_reasons_note = f"Loan capped at ₹{recommended_amount:,} based on your income (scheme max: ₹{scheme['max_amount']:,})"
        # Add as a note, not a rejection
        if score >= _PARTIAL:
            eligible_reasons.append(eligible_reasons_note)

    # ── CIBIL hard block ─────────────────────────────────────────────────────
    if scheme.get("requires_cibil") and not has_bank:
        score = min(score, _PARTIAL - 1)   # force to rejected tier

    # ── Disposable income / affordability penalty ─────────────────────────────
    if fin_status == "no_disposable":
        score = 0
        rejection_reasons.append("No disposable income — all income consumed by expenses")
        improvement_suggestions.append("Reduce monthly expenses before considering any loan")
    elif fin_status == "unsafe":
        score = min(score, _PARTIAL - 1)
        rejection_reasons.append(f"Disposable income ₹{disposable_income:,.0f}/mo is too low to safely service EMI")
        improvement_suggestions.append("Aim to reduce expenses so at least ₹2,000/mo is available after expenses")
    else:
        # Check if even the cheapest EMI (longest tenure) exceeds safe limit
        cheapest_emi = calc_emi(recommended_amount, scheme["interest_rate"], 36)["emi"]
        if cheapest_emi > safe_emi_limit and safe_emi_limit > 0:
            score = max(0, score - 20)
            rejection_reasons.append(
                f"Lowest possible EMI ₹{cheapest_emi:,.0f}/mo exceeds your safe limit ₹{safe_emi_limit:,.0f}/mo"
            )
            improvement_suggestions.append("Reduce expenses to increase disposable income before taking this loan")

    # ── Determine tier label ─────────────────────────────────────────────────
    if score >= _ELIGIBLE:
        tier = "eligible"
    elif score >= _PARTIAL:
        tier = "partial"
    else:
        tier = "rejected"

    # Deduplicate suggestions
    improvement_suggestions = list(dict.fromkeys(improvement_suggestions))

    # ── EMI options ───────────────────────────────────────────────────────────
    emi_data = build_emi_options(recommended_amount, scheme["interest_rate"], safe_emi_limit)

    return {
        "id":                      scheme["id"],
        "name":                    scheme["name"],
        "provider_type":           scheme["provider_type"],
        "max_amount":              scheme["max_amount"],
        "recommended_amount":      recommended_amount,
        "interest_rate":           scheme["interest_rate"],
        "description":             scheme["description"],
        "eligibility_score":       score,
        "tier":                    tier,
        "is_best_match":           False,
        "eligible_reasons":        eligible_reasons,
        "rejection_reasons":       rejection_reasons,
        "improvement_suggestions": improvement_suggestions,
        "emi_options":             emi_data["emi_options"],
        "recommended_plan":        emi_data["recommended_plan"],
        "safe_emi_limit":          safe_emi_limit,
    }
