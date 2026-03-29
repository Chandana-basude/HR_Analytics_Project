# Power BI Charts Build Guide — HR Analytics System

## Step-by-Step: Build All 8 Charts

---

### SETUP: Connect Data

**Option A — CSV Files (quick demo)**
1. Power BI Desktop → Home → Get Data → Text/CSV
2. Import all files from `powerbi/data/` folder
3. Rename each table cleanly (right-click → Rename)

**Option B — Live MySQL**
1. Install MySQL ODBC 8.x (64-bit)
2. Get Data → MySQL database → localhost / hr_analytics
3. Select: `employee_attrition`, `employees`, all `v_` views

---

## Chart 1 — Bar Chart: Attrition by Department

| Setting | Value |
|---------|-------|
| Visual | Clustered Bar Chart |
| Y-Axis | Department |
| X-Axis (Values) | Attrited (Sum), Total (Sum) |
| Legend | Series |
| Data Table | `attrition_by_dept` |
| Colors | Attrited = #ef4444, Total = #3b82f6 |

**DAX Measure (add to model):**
```
AttritionRate = DIVIDE(SUM(attrition_by_dept[Attrited]), SUM(attrition_by_dept[Total]), 0) * 100
```

---

## Chart 2 — Donut Chart: Overall Attrition Split

| Setting | Value |
|---------|-------|
| Visual | Donut Chart |
| Values | Count of Attrition |
| Legend | Attrition (Yes/No) |
| Data Table | `attrition_main` |
| Colors | Yes = #ef4444, No = #22c55e |

---

## Chart 3 — Column Chart: Attrition by Age Group

| Setting | Value |
|---------|-------|
| Visual | Clustered Column Chart |
| X-Axis | AgeGroup |
| Y-Axis | AttritionRate |
| Data Table | `attrition_by_age` |
| Sort | By AgeGroup ascending |
| Color | Gradient: green → red |

**Sort Order Fix (add calculated column):**
```
AgeSortOrder = SWITCH(attrition_by_age[AgeGroup],
    "Under 25", 1, "25-34", 2, "35-44", 3, "45-54", 4, "55+", 5)
```

---

## Chart 4 — Stacked Bar: Salary Band vs Attrition

| Setting | Value |
|---------|-------|
| Visual | Stacked Bar Chart |
| Y-Axis | SalaryBand |
| X-Axis | Attrited, (Total - Attrited) |
| Data Table | `attrition_by_salary` |
| Title | "Salary Band Impact on Attrition" |

**Stayed Measure:**
```
Stayed = SUM(attrition_by_salary[Total]) - SUM(attrition_by_salary[Attrited])
```

---

## Chart 5 — Pie Chart: Overtime Impact

| Setting | Value |
|---------|-------|
| Visual | Pie Chart |
| Values | Attrited |
| Legend | OverTime (Yes/No) |
| Data Table | `attrition_by_overtime` |
| Colors | Yes = #ef4444, No = #3b82f6 |

**Add Data Label:** Show AttritionRate%

---

## Chart 6 — Horizontal Bar: Attrition by Job Role

| Setting | Value |
|---------|-------|
| Visual | Horizontal Bar Chart |
| Y-Axis | JobRole |
| X-Axis | AttritionRate |
| Data Table | `attrition_by_jobrole` |
| Sort | Descending by AttritionRate |
| Color | Conditional: >25% = Red, 15-25% = Orange, <15% = Green |

**Conditional Color (via Format → Data Colors → fx):**
```
Color Rule = IF([AttritionRate] > 25, "#ef4444",
              IF([AttritionRate] > 15, "#f59e0b", "#22c55e"))
```

---

## Chart 7 — Line Chart: Job Satisfaction vs Attrition

| Setting | Value |
|---------|-------|
| Visual | Line Chart |
| X-Axis | SatisfactionLevel |
| Y-Axis | AttritionRate |
| Data Table | `attrition_by_satisfaction` |
| Markers | On |
| Stroke | #2563eb, 3px |

---

## Chart 8 — KPI Cards (4 cards)

Create 4 Card visuals:

| Card | Measure | Format |
|------|---------|--------|
| Total Employees | COUNT(EmployeeNumber) | #,0 |
| Attrition Rate | DIVIDE(COUNTIF Attrition="Yes", COUNT, 0)*100 | 0.0"%" |
| Avg Monthly Salary | AVERAGE(MonthlyIncome) | "₹"#,0 |
| Avg Years at Company | AVERAGE(YearsAtCompany) | 0.0 |

**Attrition Rate DAX:**
```
AttritionRateKPI = 
DIVIDE(
    CALCULATE(COUNT(attrition_main[Attrition]), attrition_main[Attrition] = "Yes"),
    COUNT(attrition_main[Attrition]),
    0
) * 100
```

---

## Dashboard Layout

Arrange visuals in this 3-row layout:

```
┌─────────┬─────────┬─────────┬─────────┐
│  CARD   │  CARD   │  CARD   │  CARD   │  Row 1: KPI Cards
├─────────┴────┬────┴─────────┴─────────┤
│  Bar:Dept    │    Donut: Split        │  Row 2
├──────────────┼────────────────────────┤
│  Col:Age     │    Bar: Salary         │  Row 3
├──────────────┼────────────────────────┤
│  Pie:OT      │    Bar: JobRole        │  Row 4
├──────────────┴────────────────────────┤
│        Line: Satisfaction             │  Row 5
└───────────────────────────────────────┘
```

---

## Theme & Styling

Apply this custom theme JSON in Power BI:
View → Themes → Browse → Use `powerbi/hr_analytics_theme.json`

Key settings:
- Background: #0d1117 (dark)
- Text: #e6edf3
- Accent: #2563eb
- Font: Segoe UI

---

## Publish & Embed in Flask

1. **Save** the .pbix as `powerbi/dashboard.pbix`
2. **Publish**: Home → Publish → Select workspace
3. Go to **app.powerbi.com** → Your workspace → Open report
4. **Share**: File → Embed report → Website or portal → Create embed code
5. Copy the **Page URL** (format: `https://app.powerbi.com/reportEmbed?reportId=...`)
6. In your Flask app, go to `/hr/powerbi-setup`
7. Paste the URL → Save
8. The Power BI tab in the HR Dashboard will now show your live report!

---

## Alternative: Publish to Web (Public — no login needed)

1. Open report in app.powerbi.com
2. File → **Publish to web (public)**
3. Create embed code → Copy `<iframe>` code
4. Paste iframe `src` URL into Flask at `/hr/powerbi-setup`

> ⚠️ Public embed makes data visible to anyone with the URL. Use workspace embed for production.
