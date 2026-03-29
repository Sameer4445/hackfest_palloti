from fastapi import APIRouter, HTTPException
from models.schemas import UserApplication, ScoringResponse, CreditRecord
from ml.predictor import predictor
from database import add_application
from datetime import datetime

router = APIRouter()

def generate_explanation(score: int, data: dict) -> str:
    # Rule-based generation mimicking an LLM explanation
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

    if score > 70:
        base = "Loan Appoved. "
    elif score >= 50:
        base = "Conditional Approval. "
    else:
        base = "Loan Rejected. "

    explanation = base + "The decision was primarily driven by your " + ", and ".join(reasons[:2]) + "."
    return explanation

def get_recommendations(score: int, data: dict) -> list:
    recommendations = []
    if score > 70:
        recommendations.append("Prime NBFC Unsecured Loan (Up to ₹50,000)")
        recommendations.append("Mudra Loan - Shishu (Up to ₹50,000)")
    elif score >= 50:
        recommendations.append("Micro-finance Institutional Loan (Up to ₹15,000)")
        if data.get('has_bank_account') == 1:
            recommendations.append("Secured Bank Overdraft")
    else:
        recommendations.append("Micro-savings Group Enrollment (SHG)")
        recommendations.append("Financial Literacy Program")
        
    return recommendations

@router.post("/predict", response_model=ScoringResponse)
async def score_application(application: UserApplication):
    try:
        app_dict = application.model_dump()
        
        # Get credit score from ML model
        loan_approval, confidence_score, score, processed_data = predictor.predict(app_dict)
        
        # Determine Decision and Risk
        if loan_approval == 1:
            decision = "Loan Approved"
            risk_level = "Low" if score >= 70 else "Medium"
        else:
            decision = "Loan Rejected"
            risk_level = "High"
            
        # Get explanation and recommendations
        explanation = generate_explanation(score, processed_data)
        recommendations = get_recommendations(score, processed_data)
        
        result = ScoringResponse(
            loan_approval=loan_approval,
            confidence_score=confidence_score,
            credit_score=score,
            decision=decision,
            risk_level=risk_level,
            recommended_loan_options=recommendations,
            explanation=explanation
        )
        
        # Save to DB
        record = {
            "application": app_dict,
            "processed_data": {k: float(v) if isinstance(v, (int, float)) else v for k, v in processed_data.items()},
            "result": result.model_dump(),
            "timestamp": datetime.utcnow()
        }
        await add_application(record)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
