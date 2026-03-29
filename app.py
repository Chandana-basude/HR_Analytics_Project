"""
HR Analytics System — Flask Backend
Run: python app.py
"""

import os, sys, json
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file)
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'database'))
sys.path.insert(0, os.path.join(BASE, 'ml'))

from db_connection import execute_query

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hr_analytics_secret_2024')

# ── Power BI URL helpers ──────────────────────────────────────────────────────
POWERBI_URL_FILE = os.path.join(BASE, 'powerbi', 'embed_url.txt')

def get_powerbi_url():
    try:
        if os.path.exists(POWERBI_URL_FILE):
            with open(POWERBI_URL_FILE) as f:
                return f.read().strip()
    except Exception:
        pass
    return ''

def save_powerbi_url(url):
    os.makedirs(os.path.dirname(POWERBI_URL_FILE), exist_ok=True)
    with open(POWERBI_URL_FILE, 'w') as f:
        f.write(url.strip())

# ── Decorators ────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def hr_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'HR':
            flash('HR access only.', 'danger')
            return redirect(url_for('employee_dashboard'))
        return f(*args, **kwargs)
    return decorated

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('hr_dashboard') if session['role'] == 'HR'
                        else url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = execute_query("SELECT * FROM users WHERE email=%s", (email,), fetch=True)
        if user and check_password_hash(user[0]['password'], password):
            session.update(user_id=user[0]['id'], name=user[0]['name'], role=user[0]['role'])
            return redirect(url_for('hr_dashboard') if user[0]['role'] == 'HR'
                            else url_for('employee_dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name, email = request.form.get('name','').strip(), request.form.get('email','').strip()
        password, role = request.form.get('password',''), request.form.get('role','Employee')
        if execute_query("SELECT id FROM users WHERE email=%s", (email,), fetch=True):
            flash('Email already registered.', 'warning')
        else:
            execute_query("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                          (name, email, generate_password_hash(password), role))
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Employee ──────────────────────────────────────────────────────────────────
@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    emp = execute_query(
        "SELECT * FROM employees WHERE user_id=%s ORDER BY submitted_at DESC LIMIT 1",
        (session['user_id'],), fetch=True)
    return render_template('employee_dashboard.html', employee=emp[0] if emp else None)

@app.route('/employee/form', methods=['GET', 'POST'])
@login_required
def employee_form():
    if request.method == 'POST':
        data = {
            'Age': int(request.form.get('age', 30)),
            'Gender': request.form.get('gender', 'Male'),
            'Department': request.form.get('department', 'Research & Development'),
            'JobRole': request.form.get('job_role', 'Sales Executive'),
            'MonthlyIncome': float(request.form.get('monthly_income', 5000)),
            'YearsAtCompany': int(request.form.get('years_at_company', 3)),
            'OverTime': request.form.get('overtime', 'No'),
            'JobSatisfaction': int(request.form.get('job_satisfaction', 3)),
            'WorkLifeBalance': int(request.form.get('work_life_balance', 3)),
            'DistanceFromHome': int(request.form.get('distance_from_home', 5)),
            'YearsSinceLastPromotion': int(request.form.get('years_since_last_promotion', 1)),
            'NumCompaniesWorked': int(request.form.get('num_companies_worked', 1)),
            'Education': int(request.form.get('education', 3)),
            'EnvironmentSatisfaction': int(request.form.get('environment_satisfaction', 3)),
            'RelationshipSatisfaction': int(request.form.get('relationship_satisfaction', 3)),
            'BusinessTravel': request.form.get('business_travel', 'Travel_Rarely'),
            'MaritalStatus': request.form.get('marital_status', 'Single'),
            'PercentSalaryHike': int(request.form.get('percent_salary_hike', 11)),
            'PerformanceRating': int(request.form.get('performance_rating', 3)),
            'StockOptionLevel': int(request.form.get('stock_option_level', 0)),
            'TotalWorkingYears': int(request.form.get('total_working_years', 5)),
            'TrainingTimesLastYear': int(request.form.get('training_times_last_year', 2)),
            'JobInvolvement': int(request.form.get('job_involvement', 3)),
            'JobLevel': int(request.form.get('job_level', 1)),
            'YearsInCurrentRole': int(request.form.get('years_in_current_role', 2)),
            'YearsWithCurrManager': int(request.form.get('years_with_curr_manager', 2)),
        }
        try:
            from train_model import predict_single
            result = predict_single(data)
        except Exception as e:
            result = {'prediction': 'N/A', 'probability': 0,
                      'risk_level': 'N/A', 'insights': [f'Model not loaded: {e}']}
        execute_query(
            """INSERT INTO employees
               (user_id,age,gender,department,job_role,monthly_income,years_at_company,
                overtime,job_satisfaction,work_life_balance,distance_from_home,
                years_since_last_promotion,num_companies_worked,education,
                environment_satisfaction,relationship_satisfaction,
                attrition_prediction,attrition_probability,risk_level)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (session['user_id'], data['Age'], data['Gender'], data['Department'],
             data['JobRole'], data['MonthlyIncome'], data['YearsAtCompany'],
             data['OverTime'], data['JobSatisfaction'], data['WorkLifeBalance'],
             data['DistanceFromHome'], data['YearsSinceLastPromotion'],
             data['NumCompaniesWorked'], data['Education'],
             data['EnvironmentSatisfaction'], data['RelationshipSatisfaction'],
             result['prediction'], result['probability'], result['risk_level']))
        return render_template('result.html', result=result, data=data)
    return render_template('employee_form.html')

# ── HR ────────────────────────────────────────────────────────────────────────
@app.route('/hr/dashboard')
@login_required
@hr_required
def hr_dashboard():
    stats = _get_dashboard_stats()
    employees = execute_query(
        """SELECT e.*, u.name, u.email FROM employees e
           JOIN users u ON e.user_id=u.id
           ORDER BY e.submitted_at DESC LIMIT 50""", fetch=True) or []
    return render_template('hr_dashboard.html', stats=stats,
                           employees=employees, powerbi_url=get_powerbi_url())

@app.route('/hr/employee/<int:emp_id>')
@login_required
@hr_required
def hr_employee_detail(emp_id):
    emp = execute_query(
        "SELECT e.*,u.name,u.email FROM employees e JOIN users u ON e.user_id=u.id WHERE e.employee_id=%s",
        (emp_id,), fetch=True)
    if not emp:
        flash('Employee not found.', 'danger')
        return redirect(url_for('hr_dashboard'))
    actions = execute_query(
        "SELECT * FROM hr_actions WHERE employee_id=%s ORDER BY action_date DESC",
        (emp_id,), fetch=True) or []
    return render_template('hr_employee_detail.html', emp=emp[0], actions=actions)

@app.route('/hr/action', methods=['POST'])
@login_required
@hr_required
def hr_action():
    execute_query(
        "INSERT INTO hr_actions (employee_id,hr_id,action_type,action_notes) VALUES (%s,%s,%s,%s)",
        (request.form.get('employee_id'), session['user_id'],
         request.form.get('action_type'), request.form.get('action_notes','')))
    flash('Action logged successfully.', 'success')
    return redirect(url_for('hr_employee_detail', emp_id=request.form.get('employee_id')))

# ── Power BI Setup ─────────────────────────────────────────────────────────────
@app.route('/hr/powerbi-setup', methods=['GET', 'POST'])
@login_required
@hr_required
def powerbi_setup():
    if request.method == 'POST':
        url = request.form.get('embed_url', '').strip()
        save_powerbi_url(url)
        flash('Power BI embed URL saved! Refresh the dashboard to see your report.', 'success')
        return redirect(url_for('hr_dashboard'))
    return render_template('powerbi_setup.html', current_url=get_powerbi_url())

@app.route('/hr/powerbi-report')
@login_required
@hr_required
def powerbi_builtin_report():
    """Serve the built-in Power BI-style HTML report as a fallback."""
    report_path = os.path.join(BASE, 'powerbi', 'HR_Analytics_PowerBI_Report.html')
    return send_file(report_path, mimetype='text/html')

# ── Chart API endpoints ────────────────────────────────────────────────────────
@app.route('/api/stats')
@login_required
@hr_required
def api_stats():
    return jsonify(_get_dashboard_stats())

@app.route('/api/attrition_by_dept')
@login_required
@hr_required
def api_by_dept():
    rows = execute_query(
        """SELECT Department, COUNT(*) AS total,
                  SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS attrited,
                  ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS rate
           FROM employee_attrition GROUP BY Department""", fetch=True) or []
    return jsonify(rows)

@app.route('/api/attrition_by_age')
@login_required
@hr_required
def api_by_age():
    rows = execute_query(
        """SELECT CASE WHEN Age<25 THEN 'Under 25' WHEN Age BETWEEN 25 AND 34 THEN '25-34'
                  WHEN Age BETWEEN 35 AND 44 THEN '35-44' WHEN Age BETWEEN 45 AND 54 THEN '45-54'
                  ELSE '55+' END AS AgeGroup,
                  COUNT(*) AS Total,
                  SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
                  ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS AttritionRate
           FROM employee_attrition GROUP BY AgeGroup""", fetch=True) or []
    return jsonify(rows)

@app.route('/api/attrition_by_overtime')
@login_required
@hr_required
def api_by_overtime():
    rows = execute_query(
        """SELECT OverTime, COUNT(*) AS Total,
                  SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
                  ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS AttritionRate
           FROM employee_attrition GROUP BY OverTime""", fetch=True) or []
    return jsonify(rows)

@app.route('/api/attrition_by_salary')
@login_required
@hr_required
def api_by_salary():
    rows = execute_query(
        """SELECT CASE WHEN MonthlyIncome<3000 THEN 'Under ₹3K'
                  WHEN MonthlyIncome<6000 THEN '₹3K–6K'
                  WHEN MonthlyIncome<10000 THEN '₹6K–10K'
                  ELSE 'Above ₹10K' END AS SalaryBand,
                  COUNT(*) AS Total,
                  SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
                  ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS AttritionRate
           FROM employee_attrition GROUP BY SalaryBand ORDER BY MIN(MonthlyIncome)""", fetch=True) or []
    return jsonify(rows)

@app.route('/api/attrition_by_jobrole')
@login_required
@hr_required
def api_by_jobrole():
    rows = execute_query(
        """SELECT JobRole, COUNT(*) AS Total,
                  SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
                  ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS AttritionRate
           FROM employee_attrition GROUP BY JobRole ORDER BY AttritionRate DESC""", fetch=True) or []
    return jsonify(rows)

@app.route('/api/attrition_by_satisfaction')
@login_required
@hr_required
def api_by_satisfaction():
    rows = execute_query(
        """SELECT JobSatisfaction AS Level, COUNT(*) AS Total,
                  SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
                  ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS AttritionRate
           FROM employee_attrition GROUP BY JobSatisfaction ORDER BY JobSatisfaction""", fetch=True) or []
    return jsonify(rows)

@app.route('/api/attrition_by_wlb')
@login_required
@hr_required
def api_by_wlb():
    rows = execute_query(
        """SELECT WorkLifeBalance AS Level, COUNT(*) AS Total,
                  SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS Attrited,
                  ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS AttritionRate
           FROM employee_attrition GROUP BY WorkLifeBalance ORDER BY WorkLifeBalance""", fetch=True) or []
    return jsonify(rows)

@app.route('/api/risk_distribution')
@login_required
@hr_required
def api_risk():
    rows = execute_query(
        "SELECT risk_level, COUNT(*) AS count FROM employees WHERE risk_level IS NOT NULL GROUP BY risk_level",
        fetch=True) or []
    return jsonify(rows)

# ── Helper ────────────────────────────────────────────────────────────────────
def _get_dashboard_stats():
    total    = (execute_query("SELECT COUNT(*) AS c FROM employee_attrition", fetch=True) or [{'c':0}])[0]['c']
    attrited = (execute_query("SELECT COUNT(*) AS c FROM employee_attrition WHERE Attrition='Yes'", fetch=True) or [{'c':0}])[0]['c']
    high_risk= (execute_query("SELECT COUNT(*) AS c FROM employees WHERE risk_level='High'", fetch=True) or [{'c':0}])[0]['c']
    avg_sal  = (execute_query("SELECT ROUND(AVG(MonthlyIncome),0) AS avg FROM employee_attrition", fetch=True) or [{'avg':0}])[0]['avg']
    return {
        'total_employees': total,
        'attrition_count': attrited,
        'attrition_rate': round(attrited/total*100, 1) if total else 0,
        'high_risk_employees': high_risk,
        'avg_monthly_income': avg_sal
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
