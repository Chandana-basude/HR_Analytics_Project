"""
HR Analytics System — Import IBM HR Dataset into MySQL
Run AFTER: schema.sql has been executed
Usage: python import_dataset.py
"""

import os
import sys
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, '..', 'database'))
from db_connection import get_connection, execute_query

CSV_PATH = os.path.join(BASE, '..', 'dataset', 'IBM_HR_Attrition.csv')

COLUMNS = [
    'Age','Attrition','BusinessTravel','DailyRate','Department',
    'DistanceFromHome','Education','EducationField','EmployeeCount',
    'EmployeeNumber','EnvironmentSatisfaction','Gender','HourlyRate',
    'JobInvolvement','JobLevel','JobRole','JobSatisfaction','MaritalStatus',
    'MonthlyIncome','MonthlyRate','NumCompaniesWorked','Over18','OverTime',
    'PercentSalaryHike','PerformanceRating','RelationshipSatisfaction',
    'StandardHours','StockOptionLevel','TotalWorkingYears',
    'TrainingTimesLastYear','WorkLifeBalance','YearsAtCompany',
    'YearsInCurrentRole','YearsSinceLastPromotion','YearsWithCurrManager'
]

INSERT_SQL = """
INSERT INTO employee_attrition (
    Age,Attrition,BusinessTravel,DailyRate,Department,DistanceFromHome,
    Education,EducationField,EmployeeCount,EmployeeNumber,EnvironmentSatisfaction,
    Gender,HourlyRate,JobInvolvement,JobLevel,JobRole,JobSatisfaction,MaritalStatus,
    MonthlyIncome,MonthlyRate,NumCompaniesWorked,Over18,OverTime,PercentSalaryHike,
    PerformanceRating,RelationshipSatisfaction,StandardHours,StockOptionLevel,
    TotalWorkingYears,TrainingTimesLastYear,WorkLifeBalance,YearsAtCompany,
    YearsInCurrentRole,YearsSinceLastPromotion,YearsWithCurrManager
) VALUES (
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
)
"""

def run():
    if not os.path.exists(CSV_PATH):
        print(f"✗ CSV not found: {CSV_PATH}")
        print("  Download from: https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset")
        return

    print(f"[1] Reading {CSV_PATH} …")
    df = pd.read_csv(CSV_PATH)
    df = df[[c for c in COLUMNS if c in df.columns]]
    print(f"    ✓ {len(df)} rows loaded")

    # Check existing
    existing = execute_query("SELECT COUNT(*) AS c FROM employee_attrition", fetch=True)
    if existing and existing[0]['c'] > 0:
        ans = input(f"    ⚠ Table already has {existing[0]['c']} rows. Re-import? (y/N): ")
        if ans.strip().lower() != 'y':
            print("    Skipped.")
            return
        execute_query("TRUNCATE TABLE employee_attrition")

    print("[2] Inserting records …")
    conn = get_connection()
    if conn is None:
        print("✗ DB connection failed")
        return

    cursor = conn.cursor()
    batch = []
    for _, row in df.iterrows():
        batch.append(tuple(row.get(c, None) for c in COLUMNS))
        if len(batch) == 200:
            cursor.executemany(INSERT_SQL, batch)
            conn.commit()
            batch = []
    if batch:
        cursor.executemany(INSERT_SQL, batch)
        conn.commit()
    cursor.close()
    conn.close()

    count = execute_query("SELECT COUNT(*) AS c FROM employee_attrition", fetch=True)
    print(f"    ✓ {count[0]['c']} rows inserted into employee_attrition")
    print("\n✅ Dataset import complete!")

if __name__ == '__main__':
    run()
