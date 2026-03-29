from flask import Flask, request, jsonify
from flask_cors import CORS
from ml.predictor import predictor
from ml.recommender import recommend_schemes
from ml.recommendation_engine import run_recommendation_engine
from auth.db import init_db, SessionLocal, CreditRecord, User
from auth.security import decode_token
from auth.routes import auth_bp
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Init SQLite tables
init_db()

# Register auth blueprint
app.register_blueprint(auth_bp)


# ── helpers ──────────────────────────────────────────────────────────────────

def get_current_user_from_request():
    """Returns (user, error_response). Call before protected routes."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, (jsonify({"error": "Authentication required"}), 401)
    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        return None, (jsonify({"error": "Invalid or expired token"}), 401)
    db = SessionLocal()
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    db.close()
    if not user:
        return None, (jsonify({"error": "User not found"}), 401)
    return user, None


def _build_score_breakdown(raw_score: int, processed_data: dict) -> dict:
    """Apply financial penalties to the raw ML score and return a breakdown."""
    penalties = []
    final = raw_score

    income_stability = processed_data.get('income_stability', 0.5)
    expense_ratio    = processed_data.get('expense_ratio', 0.7)
    savings_ratio    = processed_data.get('savings_ratio', 0.1)
    monthly_income   = float(processed_data.get('monthly_income_estimate', 0))
    disposable       = float(processed_data.get('net_savings', monthly_income * (1 - expense_ratio)))

    if monthly_income == 0:
        return {"base_score": 0, "penalties": ["No income — score forced to 0"], "final_score": 0}

    if monthly_income < 3000:
        final = min(final, 20)
        penalties.append("Income below ₹3,000/mo — severe penalty applied")

    if disposable <= 0:
        final = min(final, 15)
        penalties.append("No disposable income — score capped at 15")
    elif disposable < 2000:
        penalty = min(25, int((2000 - disposable) / 100) * 3)
        final = max(0, final - penalty)
        penalties.append(f"Low disposable income (₹{disposable:,.0f}/mo) — -{penalty} pts")

    if expense_ratio > 0.85:
        final = max(0, final - 15)
        penalties.append(f"Very high expense ratio ({expense_ratio*100:.0f}%) — -15 pts")
    elif expense_ratio > 0.70:
        final = max(0, final - 7)
        penalties.append(f"High expense ratio ({expense_ratio*100:.0f}%) — -7 pts")

    if income_stability < 0.4:
        final = max(0, final - 10)
        penalties.append(f"Unstable income (variance {(1-income_stability)*100:.0f}%) — -10 pts")

    if savings_ratio < 0.05:
        final = max(0, final - 8)
        penalties.append(f"Very low savings ratio ({savings_ratio*100:.1f}%) — -8 pts")

    # Clamp 0–100
    final = max(0, min(100, final))

    return {
        "base_score":  raw_score,
        "penalties":   penalties if penalties else ["No penalties — strong financial profile"],
        "final_score": final,
    }


def generate_why_bullets(processed_data: dict, score: int) -> list:
    """Return human-readable bullet points explaining the decision."""
    bullets = []
    expense_ratio  = processed_data.get('expense_ratio', 0.7)
    savings_ratio  = processed_data.get('savings_ratio', 0.1)
    income_stab    = processed_data.get('income_stability', 0.5)
    digital_usage  = processed_data.get('digital_transaction_usage', 0)
    monthly_income = float(processed_data.get('monthly_income_estimate', 0))
    disposable     = float(processed_data.get('net_savings', monthly_income * (1 - expense_ratio)))

    if monthly_income < 3000:
        bullets.append(f"Income ₹{monthly_income:,.0f}/mo is below the minimum threshold of ₹3,000")
    if disposable <= 0:
        bullets.append("All income is consumed by expenses — no money left for EMI payments")
    elif disposable < 2000:
        bullets.append(f"Disposable income ₹{disposable:,.0f}/mo is too low to safely service a loan")
    if expense_ratio > 0.80:
        bullets.append(f"Expenses consume {expense_ratio*100:.0f}% of income — leaves very little buffer")
    if savings_ratio < 0.05:
        bullets.append(f"Savings rate is only {savings_ratio*100:.1f}% — financial resilience is low")
    if income_stab < 0.45:
        bullets.append("Income is highly variable — increases repayment risk")
    if digital_usage < 0.2:
        bullets.append("Low digital transaction history — harder to verify financial behaviour")
    if score >= 70:
        bullets.append("Strong overall financial profile supports loan approval")
    elif score >= 50:
        bullets.append("Moderate financial profile — conditional approval with caution")

    return bullets or ["Mixed financial indicators — further review recommended"]


def generate_explanation(score: int, data: dict) -> str:
    reasons = []
    if data.get('income_stability', 0) > 0.7:
        reasons.append("highly stable income")
    elif data.get('income_stability', 0) < 0.4:
        reasons.append("high income variance")
    if data.get('expense_ratio', 1) < 0.6:
        reasons.append("responsible expense management")
    elif data.get('expense_ratio', 1) > 0.8:
        reasons.append("high expense-to-income ratio")
    if data.get('savings_ratio', 0) > 0.15:
        reasons.append("strong savings habits")
    elif data.get('savings_ratio', 0) < 0.05:
        reasons.append("very limited savings")
    if data.get('digital_transaction_usage', 0) > 0.6:
        reasons.append("good digital transaction history")
    if not reasons:
        reasons.append("mixed financial behavioral indicators")
    base = "Loan Approved. " if score > 70 else ("Conditional Approval. " if score >= 50 else "Loan Rejected. ")
    return base + "The decision was primarily driven by your " + ", and ".join(reasons[:2]) + "."


def get_recommendations(score: int, data: dict) -> list:
    if score > 70:
        return ["Prime NBFC Unsecured Loan (Up to ₹50,000)", "Mudra Loan - Shishu (Up to ₹50,000)"]
    elif score >= 50:
        recs = ["Micro-finance Institutional Loan (Up to ₹15,000)"]
        if data.get('has_bank_account') == 1:
            recs.append("Secured Bank Overdraft")
        return recs
    return ["Micro-savings Group Enrollment (SHG)", "Financial Literacy Program"]


# ── routes ───────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "NanoCredit AI Backend is running"})


@app.route("/api/predict", methods=["POST"])
def score_application():
    user, err = get_current_user_from_request()
    if err:
        return err

    try:
        app_dict = request.get_json()

        # ── Income guardrails (pre-ML) ────────────────────────────────────────
        raw_income = float(app_dict.get('avg_daily_income') or 0) * float(app_dict.get('work_days_per_month') or 26)
        if raw_income == 0:
            return jsonify({"error": "No income available. Please provide valid income details."}), 400
        if raw_income < 3000:
            return jsonify({
                "loan_approval": 0, "confidence_score": 0.0, "credit_score": 0,
                "decision": "Loan Rejected", "risk_level": "High",
                "explanation": "Income is below ₹3,000/month — the minimum required to be considered for any loan.",
                "recommended_loan_options": [],
                "top_schemes": [], "partial_schemes": [],
                "rejected_schemes": [],
                "score_breakdown": {"base_score": 0, "penalties": ["Income below ₹3,000/mo"], "final_score": 0},
                "why_bullets": ["Monthly income ₹{:,.0f} is below the ₹3,000 minimum threshold".format(raw_income)],
                "financial_status": "low_income",
                "warning_message": "Income too low — we do not recommend taking a loan at this time.",
                "disposable_income": 0, "safe_emi_limit": 0, "max_loan_allowed": 0,
                "recommended_amount_range": {"min": 0, "max": 0},
            })

        loan_approval, confidence_score, raw_score, processed_data = predictor.predict(app_dict)

        # ── Score normalization + penalty breakdown ───────────────────────────
        breakdown   = _build_score_breakdown(raw_score, processed_data)
        score       = breakdown["final_score"]
        loan_approval = 1 if score >= 50 else 0

        decision   = "Loan Approved" if loan_approval == 1 else "Loan Rejected"
        risk_level = ("Low" if score >= 70 else "Medium") if loan_approval == 1 else "High"
        explanation = generate_explanation(score, processed_data)
        why_bullets = generate_why_bullets(processed_data, score)

        # Smart recommendation engine (uses processed_data which has derived fields)
        rec = run_recommendation_engine(processed_data, score, risk_level)

        # System-level warning
        warning = rec.get("warning_message")
        if not warning and score < 40:
            warning = "We do not recommend taking a loan at this time based on your financial profile."

        legacy_options = [s["name"] for s in rec["top_schemes"]] or get_recommendations(score, processed_data)

        result_dict = {
            "loan_approval":            loan_approval,
            "confidence_score":         round(score / 100, 2),
            "credit_score":             score,
            "decision":                 decision,
            "risk_level":               risk_level,
            "explanation":              explanation,
            "recommended_loan_options": legacy_options,
            "score_breakdown":          breakdown,
            "why_bullets":              why_bullets,
            "top_schemes":              rec["top_schemes"],
            "partial_schemes":          rec["partial_schemes"],
            "rejected_schemes":         rec["rejected_schemes"],
            "recommended_amount_range": rec["recommended_amount_range"],
            "monthly_income":           rec["monthly_income"],
            "monthly_expense":          rec["monthly_expense"],
            "disposable_income":        rec["disposable_income"],
            "safe_emi_limit":           rec["safe_emi_limit"],
            "max_loan_allowed":         rec["max_loan_allowed"],
            "financial_status":         rec["financial_status"],
            "warning_message":          warning,
        }

        # Save to SQLite
        db = SessionLocal()
        try:
            record = CreditRecord(
                user_id=user.id,
                credit_score=score,
                decision=decision,
                risk_level=risk_level,
                confidence_score=confidence_score,
                explanation=explanation,
                recommended_loan_options=json.dumps(legacy_options),
                application_data=json.dumps({
                    **app_dict,
                    "top_schemes":      rec["top_schemes"],
                    "partial_schemes":  rec["partial_schemes"],
                    "rejected_schemes": rec["rejected_schemes"],
                }),
                created_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        return jsonify(result_dict)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """Return credit score history for the logged-in user."""
    user, err = get_current_user_from_request()
    if err:
        return err

    db = SessionLocal()
    try:
        records = db.query(CreditRecord).filter(
            CreditRecord.user_id == user.id
        ).order_by(CreditRecord.created_at.desc()).all()

        return jsonify([{
            "id": r.id,
            "credit_score": r.credit_score,
            "decision": r.decision,
            "risk_level": r.risk_level,
            "confidence_score": r.confidence_score,
            "explanation": r.explanation,
            "recommended_loan_options": json.loads(r.recommended_loan_options or "[]"),
            "application_data": json.loads(r.application_data or "{}"),
            "created_at": r.created_at.isoformat()
        } for r in records])
    finally:
        db.close()


@app.route("/api/admin/applications", methods=["GET"])
def admin_all_applications():
    """Admin: view all applications across all users."""
    user, err = get_current_user_from_request()
    if err:
        return err
    if user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    db = SessionLocal()
    try:
        records = db.query(CreditRecord, User).join(
            User, CreditRecord.user_id == User.id
        ).order_by(CreditRecord.created_at.desc()).all()

        return jsonify([{
            "id": r.id,
            "user": {"id": u.id, "name": u.name, "email": u.email},
            "credit_score": r.credit_score,
            "decision": r.decision,
            "risk_level": r.risk_level,
            "confidence_score": r.confidence_score,
            "created_at": r.created_at.isoformat()
        } for r, u in records])
    finally:
        db.close()


@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    """Admin: risk distribution and summary stats."""
    user, err = get_current_user_from_request()
    if err:
        return err
    if user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    db = SessionLocal()
    try:
        records = db.query(CreditRecord).all()
        total = len(records)
        approved = sum(1 for r in records if "Approved" in r.decision)
        risk_dist = {"Low": 0, "Medium": 0, "High": 0}
        for r in records:
            if r.risk_level in risk_dist:
                risk_dist[r.risk_level] += 1
        avg_score = round(sum(r.credit_score for r in records) / total, 1) if total else 0

        return jsonify({
            "total_applications": total,
            "approved": approved,
            "rejected": total - approved,
            "approval_rate": round(approved / total * 100, 1) if total else 0,
            "avg_credit_score": avg_score,
            "risk_distribution": risk_dist
        })
    finally:
        db.close()


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
