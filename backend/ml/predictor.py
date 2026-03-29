import os
import joblib # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore

class CreditPredictor:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        model_path = os.path.join(backend_dir, 'credit_model.pkl')
        scaler_path = os.path.join(backend_dir, 'scaler.pkl')
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            print("Successfully loaded credit_model.pkl and scaler.pkl")
        except FileNotFoundError:
            print("Credit model or scaler not found.")
            self.model = None
            self.scaler = None

    def calculate_derived_features(self, data: dict):
        monthly_income_estimate = np.float32(data.get('monthly_income_estimate', data.get('avg_daily_income', 0) * data.get('work_days_per_month', 30)))
        monthly_expense = np.float32(data.get('monthly_expense', data.get('daily_expense', 0) * 30))
        
        income_variance = np.float32(data.get('income_variance', 0.2))
        income_stability = 1 / (1 + income_variance)
        
        expense_ratio = monthly_expense / monthly_income_estimate if monthly_income_estimate > 0 else 0.9
        net_savings = monthly_income_estimate - monthly_expense
        savings_amount = max(0, net_savings)
        savings_ratio = savings_amount / monthly_income_estimate if monthly_income_estimate > 0 else 0.0
        
        financial_stability_score_raw = (income_stability * 40) + ((1 - expense_ratio) * 40) + (savings_ratio * 20)
        financial_stability_score = max(0, min(100, int(financial_stability_score_raw * 100)))
        risk_index = max(0.0, min(1.0, 1.0 - (financial_stability_score / 100.0)))

        derived = {
            'monthly_income_estimate': monthly_income_estimate,
            'income_stability': income_stability,
            'expense_ratio': expense_ratio,
            'net_savings': net_savings,
            'savings_amount': savings_amount,
            'savings_ratio': savings_ratio,
            'financial_stability_score': financial_stability_score,
            'risk_index': risk_index
        }
        
        final_data = {**data, **derived}
        final_data.pop('user_id', None)
        return final_data

    def predict(self, input_data: dict):
        if self.model is None or self.scaler is None:
            raise ValueError("Model or scaler not loaded.")
            
        processed_data = self.calculate_derived_features(input_data)

        # Build feature dict matching training columns (excluding user_id and loan_status)
        digital_usage = processed_data.get('digital_transaction_usage', 0)
        features = {
            'age': processed_data.get('age', 30),
            'occupation': processed_data.get('occupation', 'Street Vendor'),
            'location_type': processed_data.get('location_type', 'Urban'),
            'avg_daily_income': processed_data.get('avg_daily_income', 0),
            'monthly_income_estimate': processed_data.get('monthly_income_estimate', 0),
            'income_variance': processed_data.get('income_variance', 0.2),
            'income_stability': processed_data.get('income_stability', 0.5),
            'income_source_type': processed_data.get('income_source_type', 'Cash'),
            'daily_expense': processed_data.get('daily_expense', 0),
            'monthly_expense': processed_data.get('monthly_expense', processed_data.get('daily_expense', 0) * 30),
            'expense_ratio': processed_data.get('expense_ratio', 0.9),
            'essential_spending_ratio': 0.7,  # default estimate
            'savings_amount': processed_data.get('savings_amount', 0),
            'savings_ratio': processed_data.get('savings_ratio', 0),
            'has_bank_account': processed_data.get('has_bank_account', 0),
            'digital_transaction_usage': digital_usage,
            'work_days_per_month': processed_data.get('work_days_per_month', 26),
            'avg_work_hours_per_day': processed_data.get('avg_work_hours_per_day', 8),
            'location_consistency': processed_data.get('location_consistency', 0.5),
            'upi_transaction_frequency': digital_usage * 50,  # estimated from usage rate
            'net_savings': processed_data.get('net_savings', 0),
            'financial_stability_score': processed_data.get('financial_stability_score', 50),
            'risk_index': processed_data.get('risk_index', 0.5),
        }

        df = pd.DataFrame([features])
        
        # Transform using the preprocessor (ColumnTransformer)
        X_scaled = self.scaler.transform(df)
        
        # Predict probability
        probabilities = self.model.predict_proba(X_scaled)[0]
        prob_approve = probabilities[1]
        
        loan_status = 1 if prob_approve > 0.5 else 0
        confidence_score = float(prob_approve)
        score_100 = int(prob_approve * 100)
        
        return loan_status, confidence_score, score_100, processed_data

predictor = CreditPredictor()
