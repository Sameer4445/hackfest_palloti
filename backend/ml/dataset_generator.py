import pandas as pd
import numpy as np
import uuid
import os

def generate_dataset(num_rows=5000, output_path="synthetic_credit_data.csv"):
    np.random.seed(42)
    
    # Basic info
    user_id = [str(uuid.uuid4()) for _ in range(num_rows)]
    age = np.random.randint(18, 65, size=num_rows)
    occupations = ["Street Vendor", "Gig Driver", "Construction Worker", "Cleaner", "Tailor", "Delivery Agent"]
    occupation = np.random.choice(occupations, size=num_rows)
    location_type = np.random.choice(["Urban", "Semi-Urban", "Rural"], size=num_rows, p=[0.5, 0.3, 0.2])
    
    # Income Features
    avg_daily_income = np.random.uniform(200, 1500, size=num_rows)
    work_days_per_month = np.random.randint(15, 31, size=num_rows)
    monthly_income_estimate = avg_daily_income * work_days_per_month
    
    # Income variance (higher means less stable)
    income_variance = np.random.uniform(0.1, 0.5, size=num_rows) 
    # Add noise based on occupation (e.g., Street vendor has higher variance than Cleaner)
    for i in range(num_rows):
        if occupation[i] in ["Street Vendor", "Delivery Agent"]:
            income_variance[i] += np.random.uniform(0.1, 0.3)
            
    income_stability = 1 / (1 + income_variance)
    income_source_type = np.random.choice(["Cash", "Digital", "Mixed"], size=num_rows, p=[0.4, 0.2, 0.4])
    
    # Expense Features
    expense_ratios = np.random.beta(a=5, b=2, size=num_rows) * 0.9 # Most people spend a lot
    monthly_expense = monthly_income_estimate * expense_ratios
    daily_expense = monthly_expense / 30
    expense_ratio = monthly_expense / monthly_income_estimate
    
    essential_spending_ratio = np.random.uniform(0.5, 0.9, size=num_rows) # Proportion of expenses on essentials
    
    # Savings Features
    net_savings = monthly_income_estimate - monthly_expense
    savings_amount = np.where(net_savings > 0, net_savings, 0)
    savings_ratio = savings_amount / monthly_income_estimate
    
    has_bank_account = np.random.choice([0, 1], size=num_rows, p=[0.3, 0.7])
    digital_transaction_usage = np.random.uniform(0, 1, size=num_rows)
    
    # Adjustment: if mainly cash, lower digital usage
    digital_transaction_usage = np.where(income_source_type == "Cash", digital_transaction_usage * 0.3, digital_transaction_usage)
    digital_transaction_usage = np.where(income_source_type == "Digital", np.clip(digital_transaction_usage + 0.4, 0, 1), digital_transaction_usage)
    
    # Behavioral Features
    avg_work_hours_per_day = np.random.uniform(6, 14, size=num_rows)
    location_consistency = np.random.uniform(0.2, 1.0, size=num_rows) # 1.0 means always in same spot
    upi_transaction_frequency = np.random.randint(0, 100, size=num_rows) * digital_transaction_usage
    
    # Derived Features
    # Financial Stability Score (0-100)
    financial_stability_score = (income_stability * 40) + ((1 - expense_ratio) * 40) + (savings_ratio * 20)
    financial_stability_score = np.clip(financial_stability_score * 100, 0, 100)
    
    # Risk Index (0-1) - Inverse of stability, plus some randomness
    risk_index = 1 - (financial_stability_score / 100) + np.random.uniform(-0.1, 0.1, size=num_rows)
    risk_index = np.clip(risk_index, 0, 1)
    
    # Target Logic
    # High income stability + low expense ratio + high savings → loan_status = 1
    # High variance + high expenses + low savings → loan_status = 0
    
    loan_status = np.zeros(num_rows, dtype=int)
    
    for i in range(num_rows):
        prob_approval = 0.5 # Base
        
        # Stability bonus
        if income_stability[i] > 0.7: prob_approval += 0.2
        elif income_variance[i] > 0.6: prob_approval -= 0.3
            
        # Expense penalty
        if expense_ratio[i] < 0.6: prob_approval += 0.2
        elif expense_ratio[i] > 0.85: prob_approval -= 0.3
            
        # Savings bonus
        if savings_ratio[i] > 0.15: prob_approval += 0.2
        elif savings_ratio[i] < 0.05: prob_approval -= 0.1
            
        # Bank / Digital history bonus
        if has_bank_account[i]: prob_approval += 0.05
        if digital_transaction_usage[i] > 0.5: prob_approval += 0.1
        
        prob_approval = max(0.01, min(0.99, prob_approval))
        
        # Determine status deterministically to ensure clear patterns for the ML model
        # but with a tiny bit of noise
        if prob_approval > 0.55:
            loan_status[i] = 1
        elif prob_approval < 0.45:
            loan_status[i] = 0
        else:
            loan_status[i] = np.random.choice([0, 1], p=[1 - prob_approval, prob_approval])
            
    # Assembly
    data = pd.DataFrame({
        'user_id': user_id,
        'age': age,
        'occupation': occupation,
        'location_type': location_type,
        'avg_daily_income': avg_daily_income,
        'monthly_income_estimate': monthly_income_estimate,
        'income_variance': income_variance,
        'income_stability': income_stability,
        'income_source_type': income_source_type,
        'daily_expense': daily_expense,
        'monthly_expense': monthly_expense,
        'expense_ratio': expense_ratio,
        'essential_spending_ratio': essential_spending_ratio,
        'savings_amount': savings_amount,
        'savings_ratio': savings_ratio,
        'has_bank_account': has_bank_account,
        'digital_transaction_usage': digital_transaction_usage,
        'work_days_per_month': work_days_per_month,
        'avg_work_hours_per_day': avg_work_hours_per_day,
        'location_consistency': location_consistency,
        'upi_transaction_frequency': upi_transaction_frequency,
        'net_savings': net_savings,
        'financial_stability_score': financial_stability_score,
        'risk_index': risk_index,
        'loan_status': loan_status
    })
    
    # Save
    data.to_csv(output_path, index=False)
    print(f"Generated {num_rows} records and saved to {output_path}")
    print(f"Approval Rate: {data['loan_status'].mean() * 100:.1f}%")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, "synthetic_credit_data.csv")
    generate_dataset(5000, output_path)
