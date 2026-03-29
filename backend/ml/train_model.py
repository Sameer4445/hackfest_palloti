import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

def train_and_save_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, 'synthetic_credit_data.csv')
    backend_dir = os.path.dirname(current_dir)
    model_path = os.path.join(backend_dir, 'credit_model.pkl')
    scaler_path = os.path.join(backend_dir, 'scaler.pkl')
    
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}. Please run dataset_generator.py first.")
        return

    df = pd.read_csv(data_path)
    
    # Target
    y = df['loan_status']
    
    # Features - exclude ID and target
    X = df.drop(columns=['user_id', 'loan_status'])
    
    # Identify categorical and numerical columns
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    numerical_cols = X.select_dtypes(exclude=['object']).columns.tolist()
    
    print(f"Categorical features: {categorical_cols}")
    print(f"Numerical features: {len(numerical_cols)} selected.")

    # Preprocessing
    numerical_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_cols),
            ('cat', categorical_transformer, categorical_cols)
        ]
    )
    
    # Define the model pipeline
    print("Training model...")
    # Preprocessor fits and transforms data
    X_processed = preprocessor.fit_transform(X)
    
    # Split the *processed* data
    X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train
    clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10, min_samples_leaf=5)
    clf.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    
    print(f"Accuracy: {accuracy:.4f}")
    print("Classification Report:\n", report)
    
    # Save the scaler (preprocessor) and model
    joblib.dump(preprocessor, scaler_path)
    joblib.dump(clf, model_path)
    print(f"Model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")

if __name__ == "__main__":
    train_and_save_model()
