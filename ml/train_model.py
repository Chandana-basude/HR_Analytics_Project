"""
HR Analytics System - Machine Learning Model Training
Algorithms: Logistic Regression + Random Forest (ensemble)
Dataset: IBM HR Analytics Employee Attrition (1470 records)
"""

import pandas as pd
import numpy as np
import pickle
import os
import sys
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, roc_auc_score)
from sklearn.pipeline import Pipeline

# ──────────────────────────────────────────────
# 1. LOAD DATASET
# ──────────────────────────────────────────────
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'IBM_HR_Attrition.csv')
MODEL_OUT    = os.path.join(os.path.dirname(__file__), 'model.pkl')

def load_data():
    print("[1] Loading IBM HR Attrition dataset …")
    if not os.path.exists(DATASET_PATH):
        print(f"    ✗ Dataset not found at: {DATASET_PATH}")
        print("      Download from: https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset")
        sys.exit(1)
    df = pd.read_csv(DATASET_PATH)
    print(f"    ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    return df

# ──────────────────────────────────────────────
# 2. PREPROCESS
# ──────────────────────────────────────────────
FEATURES = [
    'Age', 'Department', 'DistanceFromHome', 'Education',
    'EnvironmentSatisfaction', 'Gender', 'JobInvolvement', 'JobLevel',
    'JobRole', 'JobSatisfaction', 'MaritalStatus', 'MonthlyIncome',
    'NumCompaniesWorked', 'OverTime', 'PercentSalaryHike',
    'PerformanceRating', 'RelationshipSatisfaction', 'StockOptionLevel',
    'TotalWorkingYears', 'TrainingTimesLastYear', 'WorkLifeBalance',
    'YearsAtCompany', 'YearsInCurrentRole', 'YearsSinceLastPromotion',
    'YearsWithCurrManager', 'BusinessTravel'
]

CATEGORICAL = [
    'Department', 'Gender', 'JobRole', 'MaritalStatus',
    'OverTime', 'BusinessTravel'
]

TARGET = 'Attrition'

label_encoders = {}

def preprocess(df):
    print("[2] Preprocessing data …")
    df = df.copy()

    # Drop constant / leaky columns
    drop_cols = ['EmployeeCount', 'EmployeeNumber', 'Over18', 'StandardHours']
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # Target encode
    df[TARGET] = (df[TARGET] == 'Yes').astype(int)

    # Keep only needed columns
    available = [f for f in FEATURES if f in df.columns]
    X = df[available].copy()
    y = df[TARGET]

    # Encode categoricals
    for col in CATEGORICAL:
        if col in X.columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le

    print(f"    ✓ Features used : {len(available)}")
    print(f"    ✓ Attrition=Yes : {y.sum()} ({y.mean()*100:.1f}%)")
    return X, y, available

# ──────────────────────────────────────────────
# 3. TRAIN MODELS
# ──────────────────────────────────────────────
def train(X, y):
    print("[3] Training models …")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    lr.fit(X_train_s, y_train)
    lr_acc  = accuracy_score(y_test, lr.predict(X_test_s))
    lr_auc  = roc_auc_score(y_test, lr.predict_proba(X_test_s)[:,1])
    print(f"    Logistic Regression  → Acc: {lr_acc:.4f}  AUC: {lr_auc:.4f}")

    # Random Forest
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=10, min_samples_leaf=4,
        class_weight='balanced', random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    rf_auc = roc_auc_score(y_test, rf.predict_proba(X_test)[:,1])
    print(f"    Random Forest        → Acc: {rf_acc:.4f}  AUC: {rf_auc:.4f}")

    # Gradient Boosting (best performer)
    gb = GradientBoostingClassifier(
        n_estimators=150, learning_rate=0.1, max_depth=4,
        random_state=42)
    gb.fit(X_train, y_train)
    gb_acc = accuracy_score(y_test, gb.predict(X_test))
    gb_auc = roc_auc_score(y_test, gb.predict_proba(X_test)[:,1])
    print(f"    Gradient Boosting    → Acc: {gb_acc:.4f}  AUC: {gb_auc:.4f}")

    # Choose best by AUC
    best_name, best_model, best_auc, uses_scale = max(
        [('Logistic Regression', lr, lr_auc, True),
         ('Random Forest',       rf, rf_auc, False),
         ('Gradient Boosting',   gb, gb_auc, False)],
        key=lambda x: x[2])
    print(f"\n    ★ Best model: {best_name}  (AUC={best_auc:.4f})")

    # Detailed report
    if uses_scale:
        y_pred = best_model.predict(X_test_s)
    else:
        y_pred = best_model.predict(X_test)
    print("\n    Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Stay','Leave']))

    return best_model, scaler, uses_scale, best_name

# ──────────────────────────────────────────────
# 4. FEATURE IMPORTANCE
# ──────────────────────────────────────────────
def show_importance(model, feature_names):
    if hasattr(model, 'feature_importances_'):
        imp = pd.Series(model.feature_importances_, index=feature_names)
        print("\n[4] Top-10 Feature Importances:")
        print(imp.nlargest(10).to_string())

# ──────────────────────────────────────────────
# 5. SAVE MODEL BUNDLE
# ──────────────────────────────────────────────
def save_bundle(model, scaler, uses_scale, feature_names, best_name):
    bundle = {
        'model': model,
        'scaler': scaler,
        'uses_scale': uses_scale,
        'label_encoders': label_encoders,
        'feature_names': feature_names,
        'categorical_cols': CATEGORICAL,
        'model_name': best_name
    }
    with open(MODEL_OUT, 'wb') as f:
        pickle.dump(bundle, f)
    print(f"\n[5] Model bundle saved → {MODEL_OUT}")

# ──────────────────────────────────────────────
# PREDICT HELPER  (imported by app.py)
# ──────────────────────────────────────────────
def predict_single(input_dict: dict) -> dict:
    """
    Given a dict of employee features, return:
      { 'prediction': 'Yes'/'No',
        'probability': float (0-100),
        'risk_level':  'High'/'Medium'/'Low',
        'insights':    [list of HR recommendations] }
    """
    with open(MODEL_OUT, 'rb') as f:
        bundle = pickle.load(f)

    model    = bundle['model']
    scaler   = bundle['scaler']
    uses_sc  = bundle['uses_scale']
    les      = bundle['label_encoders']
    feat_names = bundle['feature_names']
    cat_cols = bundle['categorical_cols']

    row = {}
    for feat in feat_names:
        val = input_dict.get(feat, 0)
        if feat in cat_cols and feat in les:
            le = les[feat]
            val_str = str(val)
            if val_str in le.classes_:
                val = le.transform([val_str])[0]
            else:
                val = 0
        row[feat] = val

    X = pd.DataFrame([row])[feat_names]

    if uses_sc:
        X_input = scaler.transform(X)
    else:
        X_input = X.values

    prob_leave = float(model.predict_proba(X_input)[0][1])
    prediction = 'Yes' if prob_leave >= 0.5 else 'No'

    if prob_leave >= 0.70:
        risk = 'High'
    elif prob_leave >= 0.40:
        risk = 'Medium'
    else:
        risk = 'Low'

    insights = _generate_insights(input_dict, prob_leave)

    return {
        'prediction':  prediction,
        'probability': round(prob_leave * 100, 2),
        'risk_level':  risk,
        'insights':    insights
    }

def _generate_insights(d: dict, prob: float) -> list:
    tips = []
    if int(d.get('JobSatisfaction', 3)) <= 2:
        tips.append("⚠ Low Job Satisfaction — consider role enrichment or team change.")
    if int(d.get('WorkLifeBalance', 3)) <= 2:
        tips.append("⚠ Poor Work-Life Balance — evaluate workload distribution.")
    if str(d.get('OverTime', 'No')) == 'Yes':
        tips.append("⚠ Employee works overtime regularly — consider reducing workload.")
    if float(d.get('MonthlyIncome', 5000)) < 3000:
        tips.append("⚠ Below-average salary — consider a salary increment.")
    if int(d.get('YearsSinceLastPromotion', 0)) >= 3:
        tips.append("⚠ No promotion in 3+ years — review career progression.")
    if int(d.get('EnvironmentSatisfaction', 3)) <= 2:
        tips.append("⚠ Low Environment Satisfaction — improve workplace conditions.")
    if int(d.get('DistanceFromHome', 5)) >= 20:
        tips.append("ℹ Long commute — explore remote/hybrid work options.")
    if not tips:
        tips.append("✓ Employee appears stable. Maintain current engagement programs.")
    return tips

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == '__main__':
    df = load_data()
    X, y, feat_names = preprocess(df)
    model, scaler, uses_scale, best_name = train(X, y)
    show_importance(model, feat_names)
    save_bundle(model, scaler, uses_scale, feat_names, best_name)
    print("\n✅ Training complete. Run `python app.py` to start the web server.")
