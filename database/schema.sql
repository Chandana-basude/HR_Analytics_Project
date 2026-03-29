-- ============================================================
-- HR Analytics System - Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS hr_analytics;
USE hr_analytics;

-- ============================================================
-- TABLE 1: Users (Login & Signup)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('HR', 'Employee') NOT NULL DEFAULT 'Employee',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: Employees (Form + Predictions)
-- ============================================================
CREATE TABLE IF NOT EXISTS employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    age INT,
    gender VARCHAR(10),
    department VARCHAR(100),
    job_role VARCHAR(100),
    monthly_income FLOAT,
    years_at_company INT,
    overtime VARCHAR(5),
    job_satisfaction INT,
    work_life_balance INT,
    distance_from_home INT,
    years_since_last_promotion INT,
    num_companies_worked INT,
    education INT,
    environment_satisfaction INT,
    relationship_satisfaction INT,
    attrition_prediction VARCHAR(5),
    attrition_probability FLOAT,
    risk_level VARCHAR(10),
    hr_action_taken TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- TABLE 3: IBM HR Attrition Dataset (for ML & Power BI)
-- ============================================================
CREATE TABLE IF NOT EXISTS employee_attrition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Age INT,
    Attrition VARCHAR(5),
    BusinessTravel VARCHAR(50),
    DailyRate INT,
    Department VARCHAR(100),
    DistanceFromHome INT,
    Education INT,
    EducationField VARCHAR(100),
    EmployeeCount INT,
    EmployeeNumber INT,
    EnvironmentSatisfaction INT,
    Gender VARCHAR(10),
    HourlyRate INT,
    JobInvolvement INT,
    JobLevel INT,
    JobRole VARCHAR(100),
    JobSatisfaction INT,
    MaritalStatus VARCHAR(20),
    MonthlyIncome INT,
    MonthlyRate INT,
    NumCompaniesWorked INT,
    Over18 VARCHAR(5),
    OverTime VARCHAR(5),
    PercentSalaryHike INT,
    PerformanceRating INT,
    RelationshipSatisfaction INT,
    StandardHours INT,
    StockOptionLevel INT,
    TotalWorkingYears INT,
    TrainingTimesLastYear INT,
    WorkLifeBalance INT,
    YearsAtCompany INT,
    YearsInCurrentRole INT,
    YearsSinceLastPromotion INT,
    YearsWithCurrManager INT
);

-- ============================================================
-- TABLE 4: HR Actions Log
-- ============================================================
CREATE TABLE IF NOT EXISTS hr_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    hr_id INT,
    action_type VARCHAR(100),
    action_notes TEXT,
    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (hr_id) REFERENCES users(id)
);

-- ============================================================
-- Default HR Admin Account (password: admin123)
-- ============================================================
INSERT IGNORE INTO users (name, email, password, role)
VALUES ('HR Admin', 'hr@company.com',
        'pbkdf2:sha256:260000$placeholder$hash', 'HR');

-- ============================================================
-- Useful Views for Power BI / Dashboard
-- ============================================================

CREATE OR REPLACE VIEW v_attrition_by_department AS
SELECT Department,
       COUNT(*) AS Total,
       SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) AS Attrited,
       ROUND(SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS AttritionRate
FROM employee_attrition
GROUP BY Department;

CREATE OR REPLACE VIEW v_attrition_by_salary AS
SELECT
    CASE
        WHEN MonthlyIncome < 3000 THEN 'Below 3K'
        WHEN MonthlyIncome BETWEEN 3000 AND 6000 THEN '3K-6K'
        WHEN MonthlyIncome BETWEEN 6001 AND 10000 THEN '6K-10K'
        ELSE 'Above 10K'
    END AS SalaryBand,
    COUNT(*) AS Total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) AS Attrited,
    ROUND(AVG(MonthlyIncome), 2) AS AvgSalary
FROM employee_attrition
GROUP BY SalaryBand;

CREATE OR REPLACE VIEW v_attrition_by_age AS
SELECT
    CASE
        WHEN Age < 25 THEN 'Under 25'
        WHEN Age BETWEEN 25 AND 34 THEN '25-34'
        WHEN Age BETWEEN 35 AND 44 THEN '35-44'
        WHEN Age BETWEEN 45 AND 54 THEN '45-54'
        ELSE '55+'
    END AS AgeGroup,
    COUNT(*) AS Total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) AS Attrited
FROM employee_attrition
GROUP BY AgeGroup;

CREATE OR REPLACE VIEW v_attrition_by_overtime AS
SELECT OverTime,
       COUNT(*) AS Total,
       SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) AS Attrited,
       ROUND(SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS AttritionRate
FROM employee_attrition
GROUP BY OverTime;
