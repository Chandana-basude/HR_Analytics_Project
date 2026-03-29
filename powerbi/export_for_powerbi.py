"""
HR Analytics — Power BI Data Export Script
==========================================
Exports all required tables/views from MySQL to CSV files.
Power BI Desktop can connect directly to these CSVs OR to MySQL.

Usage:
    cd HR_Analytics_Project
    python powerbi/export_for_powerbi.py

Output files (in powerbi/data/):
    attrition_main.csv         ← IBM dataset (1470 rows)
    attrition_by_dept.csv      ← dept-level aggregates
    attrition_by_age.csv       ← age group aggregates
    attrition_by_salary.csv    ← salary band aggregates
    attrition_by_overtime.csv  ← overtime impact
    attrition_by_jobrole.csv   ← job role breakdown
    live_predictions.csv       ← real employee predictions from Flask app
    monthly_trend.csv          ← trend data for line chart
"""

import os, sys
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, '..', 'database'))

try:
    from db_connection import get_connection
    USE_DB = True
except Exception:
    USE_DB = False

OUT_DIR = os.path.join(BASE, 'data')
os.makedirs(OUT_DIR, exist_ok=True)


def query_to_csv(sql, filename, conn=None):
    """Run SQL and save result as CSV."""
    try:
        df = pd.read_sql(sql, conn)
        path = os.path.join(OUT_DIR, filename)
        df.to_csv(path, index=False)
        print(f"  ✓ {filename}  ({len(df)} rows)")
        return df
    except Exception as e:
        print(f"  ✗ {filename}: {e}")
        return pd.DataFrame()


def export_from_db():
    print("\n[1] Connecting to MySQL …")
    conn = get_connection()
    if conn is None:
        print("    ✗ DB connection failed. Using sample data instead.")
        export_sample_data()
        return

    print("[2] Exporting tables …")

    # Main IBM dataset
    query_to_csv("SELECT * FROM employee_attrition", "attrition_main.csv", conn)

    # Aggregated views
    query_to_csv("""
        SELECT Department,
               COUNT(*) AS Total,
               SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
               ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS AttritionRate,
               ROUND(AVG(MonthlyIncome),0) AS AvgSalary
        FROM employee_attrition GROUP BY Department
    """, "attrition_by_dept.csv", conn)

    query_to_csv("""
        SELECT
            CASE
                WHEN Age < 25 THEN 'Under 25'
                WHEN Age BETWEEN 25 AND 34 THEN '25-34'
                WHEN Age BETWEEN 35 AND 44 THEN '35-44'
                WHEN Age BETWEEN 45 AND 54 THEN '45-54'
                ELSE '55+'
            END AS AgeGroup,
            COUNT(*) AS Total,
            SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
            ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS AttritionRate
        FROM employee_attrition
        GROUP BY AgeGroup ORDER BY FIELD(AgeGroup,'Under 25','25-34','35-44','45-54','55+')
    """, "attrition_by_age.csv", conn)

    query_to_csv("""
        SELECT
            CASE
                WHEN MonthlyIncome < 3000  THEN '1. Below ₹3K'
                WHEN MonthlyIncome < 6000  THEN '2. ₹3K–6K'
                WHEN MonthlyIncome < 10000 THEN '3. ₹6K–10K'
                ELSE '4. Above ₹10K'
            END AS SalaryBand,
            COUNT(*) AS Total,
            SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
            ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS AttritionRate,
            ROUND(AVG(MonthlyIncome),0) AS AvgIncome
        FROM employee_attrition
        GROUP BY SalaryBand ORDER BY SalaryBand
    """, "attrition_by_salary.csv", conn)

    query_to_csv("""
        SELECT OverTime,
               COUNT(*) AS Total,
               SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
               ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS AttritionRate
        FROM employee_attrition GROUP BY OverTime
    """, "attrition_by_overtime.csv", conn)

    query_to_csv("""
        SELECT JobRole,
               COUNT(*) AS Total,
               SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
               ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS AttritionRate,
               ROUND(AVG(MonthlyIncome),0) AS AvgSalary,
               ROUND(AVG(JobSatisfaction),2) AS AvgJobSatisfaction
        FROM employee_attrition GROUP BY JobRole ORDER BY AttritionRate DESC
    """, "attrition_by_jobrole.csv", conn)

    query_to_csv("""
        SELECT JobSatisfaction AS SatisfactionLevel,
               COUNT(*) AS Total,
               SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
               ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS AttritionRate
        FROM employee_attrition GROUP BY JobSatisfaction ORDER BY JobSatisfaction
    """, "attrition_by_satisfaction.csv", conn)

    query_to_csv("""
        SELECT WorkLifeBalance,
               COUNT(*) AS Total,
               SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
               ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS AttritionRate
        FROM employee_attrition GROUP BY WorkLifeBalance ORDER BY WorkLifeBalance
    """, "attrition_by_wlb.csv", conn)

    # Live predictions from Flask app
    query_to_csv("""
        SELECT e.employee_id, u.name, u.email,
               e.department, e.job_role, e.monthly_income,
               e.years_at_company, e.overtime, e.job_satisfaction,
               e.work_life_balance, e.attrition_prediction,
               e.attrition_probability, e.risk_level,
               e.submitted_at
        FROM employees e JOIN users u ON e.user_id = u.id
        ORDER BY e.submitted_at DESC
    """, "live_predictions.csv", conn)

    conn.close()
    print("\n✅ Export complete! Files saved to: powerbi/data/")
    print_powerbi_instructions()


def export_sample_data():
    """Generate realistic sample CSVs when DB is unavailable."""
    print("\n[2] Generating sample data for Power BI demo …")

    # Dept data
    pd.DataFrame({
        'Department':    ['Sales', 'Research & Development', 'Human Resources'],
        'Total':         [446, 961, 63],
        'Attrited':      [92, 133, 12],
        'AttritionRate': [20.63, 13.84, 19.05],
        'AvgSalary':     [6959, 6281, 6654]
    }).to_csv(os.path.join(OUT_DIR, 'attrition_by_dept.csv'), index=False)
    print("  ✓ attrition_by_dept.csv")

    pd.DataFrame({
        'AgeGroup':      ['Under 25','25-34','35-44','45-54','55+'],
        'Total':         [62, 534, 505, 274, 95],
        'Attrited':      [22, 112, 68, 28, 7],
        'AttritionRate': [35.5, 21.0, 13.5, 10.2, 7.4]
    }).to_csv(os.path.join(OUT_DIR, 'attrition_by_age.csv'), index=False)
    print("  ✓ attrition_by_age.csv")

    pd.DataFrame({
        'SalaryBand':    ['1. Below ₹3K','2. ₹3K–6K','3. ₹6K–10K','4. Above ₹10K'],
        'Total':         [170, 693, 396, 211],
        'Attrited':      [70, 118, 38, 11],
        'AttritionRate': [41.2, 17.0, 9.6, 5.2],
        'AvgIncome':     [2476, 4710, 7853, 15067]
    }).to_csv(os.path.join(OUT_DIR, 'attrition_by_salary.csv'), index=False)
    print("  ✓ attrition_by_salary.csv")

    pd.DataFrame({
        'OverTime':      ['No', 'Yes'],
        'Total':         [1054, 416],
        'Attrited':      [110, 127],
        'AttritionRate': [10.44, 30.53]
    }).to_csv(os.path.join(OUT_DIR, 'attrition_by_overtime.csv'), index=False)
    print("  ✓ attrition_by_overtime.csv")

    pd.DataFrame({
        'JobRole':       ['Sales Representative','Laboratory Technician','Human Resources',
                          'Sales Executive','Research Scientist','Healthcare Representative',
                          'Manufacturing Director','Manager','Research Director'],
        'Total':         [83,259,52,326,292,131,145,102,80],
        'Attrited':      [33,62,12,57,47,9,10,5,2],
        'AttritionRate': [39.8,23.9,23.1,17.5,16.1,6.9,6.9,4.9,2.5],
        'AvgSalary':     [2626,3237,4143,6924,5531,7528,7020,17201,15947]
    }).to_csv(os.path.join(OUT_DIR, 'attrition_by_jobrole.csv'), index=False)
    print("  ✓ attrition_by_jobrole.csv")

    pd.DataFrame({
        'SatisfactionLevel': [1, 2, 3, 4],
        'Label':             ['Low','Medium','High','Very High'],
        'Total':             [289,280,442,459],
        'Attrited':          [66,46,86,40],
        'AttritionRate':     [22.8,16.4,19.5,8.7]
    }).to_csv(os.path.join(OUT_DIR, 'attrition_by_satisfaction.csv'), index=False)
    print("  ✓ attrition_by_satisfaction.csv")

    pd.DataFrame({
        'WorkLifeBalance': [1,2,3,4],
        'Label':           ['Bad','Good','Better','Best'],
        'Total':           [80,344,828,218],
        'Attrited':        [25,59,127,26],
        'AttritionRate':   [31.3,17.2,15.3,11.9]
    }).to_csv(os.path.join(OUT_DIR, 'attrition_by_wlb.csv'), index=False)
    print("  ✓ attrition_by_wlb.csv")

    print("\n✅ Sample CSVs ready! Import into Power BI Desktop.")
    print_powerbi_instructions()


def print_powerbi_instructions():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          POWER BI SETUP INSTRUCTIONS                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  OPTION A — Import CSVs (easiest for demo):                  ║
║  1. Open Power BI Desktop                                     ║
║  2. Home → Get Data → Text/CSV                               ║
║  3. Import each CSV from powerbi/data/                       ║
║  4. Build charts (see powerbi/CHARTS_GUIDE.md)               ║
║                                                              ║
║  OPTION B — Live MySQL connection:                           ║
║  1. Install MySQL ODBC Connector (64-bit)                    ║
║     https://dev.mysql.com/downloads/connector/odbc/          ║
║  2. Power BI → Get Data → MySQL database                     ║
║  3. Server: localhost  Database: hr_analytics                ║
║  4. Select tables + views → Load                             ║
║                                                              ║
║  EMBED IN FLASK:                                             ║
║  1. Publish .pbix → app.powerbi.com                          ║
║  2. File → Embed report → Website or portal                  ║
║  3. Copy iframe URL                                          ║
║  4. Run Flask: python app.py                                 ║
║  5. Go to /hr/powerbi-setup → paste URL → Save               ║
║  6. Power BI tab in dashboard will show your report          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == '__main__':
    if USE_DB:
        export_from_db()
    else:
        print("DB module not found. Generating sample data …")
        export_sample_data()
