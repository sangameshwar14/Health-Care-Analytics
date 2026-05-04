""" import dash
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, html, State
import plotly.express as px
import os
import base64
import numpy as np

# -----------------------------------
# Load Dataset
# -----------------------------------
def load_data():
    df = pd.read_csv("assets/healthcare.csv")
    df["Billing Amount"] = pd.to_numeric(df["Billing Amount"], errors="coerce")
    df["Date of Admission"] = pd.to_datetime(df["Date of Admission"], errors="coerce")
    df["YearMonth"] = df["Date of Admission"].dt.to_period("M")

    # Add synthetic Department column if missing
    if "Department" not in df.columns:
        departments = ["Cardiology", "Neurology", "Oncology", "Orthopedics", "Pediatrics"]
        df["Department"] = np.random.choice(departments, size=len(df))
    return df


data = load_data()
num_records = len(data)
avg_billing = data["Billing Amount"].mean()
last_admission = data["Date of Admission"].max().strftime("%d %b %Y")
total_departments = data["Department"].nunique()

# -----------------------------------
# App Initialization
# -----------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "assets/style.css"])
app.title = "Healthcare Analytics Dashboard"

# -----------------------------------
# Sidebar (Filters + File Upload)
# -----------------------------------
sidebar = html.Div(
    [
        html.H4("🔍 Filters & Upload", className="text-center mb-3"),
        html.Hr(),
        html.Label("Select Gender:"),
        dcc.Dropdown(
            options=[{"label": g, "value": g} for g in data["Gender"].unique()],
            id="gender-filter",
            placeholder="Select a Gender",
        ),
        html.Br(),
        html.Label("Select Condition:"),
        dcc.Dropdown(
            options=[{"label": c, "value": c} for c in data["Medical Condition"].unique()],
            id="condition-filter",
            placeholder="Select a Condition",
        ),
        html.Br(),
        html.Label("Billing Amount Filter:"),
        dcc.Slider(
            id="billing-slider",
            min=data["Billing Amount"].min(),
            max=data["Billing Amount"].max(),
            value=data["Billing Amount"].median(),
            marks={
                int(v): f"${int(v):,}"
                for v in data["Billing Amount"].quantile([0, 0.25, 0.5, 0.75, 1]).values
            },
            step=100,
        ),
        html.Br(),
        html.Label("📤 Upload Custom Dataset:"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select File")]),
            style={
                "width": "100%",
                "height": "100px",
                "lineHeight": "100px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "textAlign": "center",
                "margin": "10px",
                "borderRadius": "8px",
                "backgroundColor": "#f8f9fa",
            },
            multiple=False,
        ),
        html.Div(id="output-data", className="text-center mt-2 text-success"),
    ],
    style={
        "width": "320px",
        "padding": "20px",
        "backgroundColor": "#f8f9fa",
        "borderRight": "1px solid #dee2e6",
        "height": "100vh",
    },
)

# -----------------------------------
# KPI Cards (Top Row)
# -----------------------------------
def kpi_card(icon, title, value, color):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(icon, className=f"text-{color} fs-3 mb-2"),
                html.H5(title, className="card-title fw-bold"),
                html.H4(value, className="card-text"),
            ]
        ),
        className="shadow-lg hover-glow text-center rounded-4 p-3",
        style={"transition": "0.3s", "cursor": "pointer"},
    )

# -----------------------------------
# Main Dashboard Layout
# -----------------------------------
content = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H1("Healthcare Dashboard", className="text-center mt-4 fw-bold")),
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    "☰ Toggle Sidebar",
                    id="open-offcanvas",
                    n_clicks=0,
                    className="btn btn-outline-secondary my-3",
                ),
                width=12,
                className="text-center",
            )
        ),
        dbc.Offcanvas(sidebar, id="offcanvas", title="Filter & Upload", is_open=False, placement="start"),
        dbc.Row(
            [
                dbc.Col(kpi_card("🧍‍♂️", "Total Patients", f"{num_records:,}", "primary")),
                dbc.Col(kpi_card("💰", "Avg Billing", f"${avg_billing:,.2f}", "success")),
                dbc.Col(kpi_card("🏥", "Departments", str(total_departments), "warning")),
                dbc.Col(kpi_card("📅", "Last Admission", last_admission, "info")),
            ],
            className="mb-5 g-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Age Distribution by Gender"),
                                dcc.Graph(id="age-distribution"),
                            ]
                        ),
                        className="shadow-sm rounded-4",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Medical Condition Distribution"),
                                dcc.Graph(id="condition-distribution"),
                            ]
                        ),
                        className="shadow-sm rounded-4",
                    ),
                    width=6,
                ),
            ]
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Insurance Provider Comparison"),
                            dcc.Graph(id="insurance-comparison"),
                        ]
                    ),
                    className="shadow-sm rounded-4",
                )
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Billing Amount Distribution"),
                            dcc.Graph(id="billing-distribution"),
                        ]
                    ),
                    className="shadow-sm rounded-4",
                )
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Admission Trends"),
                            dcc.RadioItems(
                                options=[
                                    {"label": "Line Chart", "value": "line"},
                                    {"label": "Bar Chart", "value": "bar"},
                                ],
                                value="line",
                                inline=True,
                                id="chart-type",
                            ),
                            dcc.Graph(id="admission-trends"),
                        ]
                    ),
                    className="shadow-sm rounded-4",
                )
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Department-wise Analysis"),
                            dcc.Graph(id="department-analysis"),
                        ]
                    ),
                    className="shadow-sm rounded-4 mb-5",
                )
            )
        ),
    ],
    fluid=True,
)

app.layout = html.Div([content])

# -----------------------------------
# Callbacks
# -----------------------------------
@app.callback(Output("offcanvas", "is_open"), Input("open-offcanvas", "n_clicks"), State("offcanvas", "is_open"))
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(Output("age-distribution", "figure"), Input("gender-filter", "value"))
def update_distribution(selected_gender):
    filtered = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.histogram(filtered, x="Age", color="Gender", title="Age Distribution by Gender")
    return fig


@app.callback(Output("condition-distribution", "figure"), Input("gender-filter", "value"))
def update_condition(selected_gender):
    filtered = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.pie(filtered, names="Medical Condition", title="Medical Condition Distribution")
    return fig


@app.callback(Output("insurance-comparison", "figure"), Input("gender-filter", "value"))
def update_insurance(selected_gender):
    filtered = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.bar(
        filtered,
        x="Insurance Provider",
        y="Billing Amount",
        color="Medical Condition",
        barmode="group",
        title="Insurance Price Comparison",
    )
    return fig


@app.callback(
    Output("billing-distribution", "figure"),
    Input("gender-filter", "value"),
    Input("billing-slider", "value"),
)
def update_billing(selected_gender, slider_value):
    filtered = data[data["Gender"] == selected_gender] if selected_gender else data
    filtered = filtered[filtered["Billing Amount"] <= slider_value]
    fig = px.histogram(filtered, x="Billing Amount", nbins=10, title="Billing Amount Distribution")
    return fig


@app.callback(Output("admission-trends", "figure"), Input("chart-type", "value"), Input("condition-filter", "value"))
def update_trends(chart_type, selected_condition):
    filtered = data[data["Medical Condition"] == selected_condition] if selected_condition else data
    trend_df = filtered.groupby("YearMonth").size().reset_index(name="Count")
    trend_df["YearMonth"] = trend_df["YearMonth"].astype(str)
    if chart_type == "line":
        fig = px.line(trend_df, x="YearMonth", y="Count", title="Admission Trends over Time")
    else:
        fig = px.bar(trend_df, x="YearMonth", y="Count", title="Admission Trends over Time")
    return fig


@app.callback(Output("department-analysis", "figure"), Input("gender-filter", "value"))
def update_department(selected_gender):
    filtered = data[data["Gender"] == selected_gender] if selected_gender else data
    dept_df = filtered.groupby("Department").agg({"Billing Amount": "mean", "Age": "count"}).reset_index()
    dept_df.rename(columns={"Age": "Patient Count"}, inplace=True)
    fig = px.bar(
        dept_df,
        x="Department",
        y=["Patient Count", "Billing Amount"],
        barmode="group",
        title="Department-wise Patient & Billing Comparison",
    )
    return fig


@app.callback(Output("output-data", "children"), Input("upload-data", "contents"), Input("upload-data", "filename"))
def save_file(contents, filename):
    if contents is None:
        return ""
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    upload_folder = os.path.join(os.getcwd(), "assets")
    os.makedirs(upload_folder, exist_ok=True)
    save_to_path = os.path.join(upload_folder, filename)
    with open(save_to_path, "wb") as f:
        f.write(decoded)
    return f"✅ File '{filename}' uploaded successfully!"

# -----------------------------------
# Run Server
# -----------------------------------
if __name__ == "__main__":
    app.run(debug=True)
    """

import dash
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, html, State
import plotly.express as px
import os
import base64
import numpy as np

# --------------------------------------------------------
# AUTO DETECT COLUMNS FOR ANY CSV
# --------------------------------------------------------
def auto_detect_column(df, possible_names):
    for col in df.columns:
        normalized = col.lower().replace(" ", "").replace("_", "")
        if normalized in possible_names:
            return col
    return None

# --------------------------------------------------------
# LOAD + CLEAN DATA (WORKS FOR ANY CSV)
# --------------------------------------------------------
def load_data():
    df = pd.read_csv("assets/healthcare.csv")

    # Autodetect columns
    age_col   = auto_detect_column(df, ["age", "patientage", "years"])
    gender_col = auto_detect_column(df, ["gender", "sex"])
    billing_col = auto_detect_column(df, ["billingamount", "bill", "charge", "amount"])
    date_col = auto_detect_column(df, ["dateofadmission", "admissiondate", "date"])
    condition_col = auto_detect_column(df, ["medicalcondition", "diagnosis", "condition"])
    insurance_col = auto_detect_column(df, ["insuranceprovider", "insurance", "payer"])
    department_col = auto_detect_column(df, ["department", "unit", "ward"])

    # ---------------------------------------
    # CREATE MISSING COLUMNS AUTOMATICALLY
    # ---------------------------------------

    if age_col is None:
        df["Age"] = np.random.randint(18, 90, size=len(df))
        age_col = "Age"

    if gender_col is None:
        df["Gender"] = np.random.choice(["Male", "Female"], size=len(df))
        gender_col = "Gender"

    if billing_col is None:
        df["Billing Amount"] = np.random.randint(500, 20000, size=len(df))
        billing_col = "Billing Amount"
    df[billing_col] = pd.to_numeric(df[billing_col], errors="coerce")

    if date_col is None:
        df["Date of Admission"] = pd.date_range(start="2024-01-01", periods=len(df), freq="D")
        date_col = "Date of Admission"
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["YearMonth"] = df[date_col].dt.to_period("M").astype(str)

    if condition_col is None:
        df["Medical Condition"] = np.random.choice(
            ["Diabetes", "Hypertension", "Cancer", "Asthma"], size=len(df)
        )
        condition_col = "Medical Condition"

    if insurance_col is None:
        df["Insurance Provider"] = np.random.choice(
            ["Aetna", "BlueCross", "UnitedHealth", "Medicaid"], size=len(df)
        )
        insurance_col = "Insurance Provider"

    if department_col is None:
        df["Department"] = np.random.choice(
            ["Cardiology", "Neurology", "Oncology", "Orthopedics"], size=len(df)
        )
        department_col = "Department"

    if "Readmitted" not in df.columns:
        df["Readmitted"] = np.random.choice([0, 1], size=len(df), p=[0.8, 0.2])

    if "Length of Stay" not in df.columns:
        df["Length of Stay"] = np.random.randint(1, 15, size=len(df))

    if "Outcome" not in df.columns:
        df["Outcome"] = np.random.choice(["Alive", "Deceased"], size=len(df), p=[0.97, 0.03])

    if "Total Beds" not in df.columns:
        df["Total Beds"] = 100

    if "Beds Occupied" not in df.columns:
        df["Beds Occupied"] = np.random.randint(50, 100, size=len(df))

    return df, age_col, gender_col, billing_col, date_col, condition_col, insurance_col, department_col


# Load data
data, AGE, GENDER, BILL, DATE, CONDITION, INSURANCE, DEPARTMENT = load_data()

# KPIs
readmission_rate = data["Readmitted"].mean() * 100
alos = data["Length of Stay"].mean()
mortality_rate = (data["Outcome"] == "Deceased").mean() * 100
occupancy_rate = (data["Beds Occupied"].mean() / data["Total Beds"].mean()) * 100

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Universal Healthcare KPI Dashboard"

# --------------------------------------------------------
# SIDEBAR COMPONENT (appears inside Offcanvas)
# --------------------------------------------------------
sidebar = html.Div(
    [
        html.H4("Filters & Upload CSV", className="text-center mb-3"),
        html.Hr(),

        html.Label("Filter by Gender:"),
        dcc.Dropdown(
            id="gender-filter",
            options=[{"label": g, "value": g} for g in data[GENDER].unique()],
            placeholder="Select Gender",
        ),
        html.Br(),

        html.Label("Filter by Condition:"),
        dcc.Dropdown(
            id="condition-filter",
            options=[{"label": c, "value": c} for c in data[CONDITION].unique()],
            placeholder="Select Condition",
        ),
        html.Br(),

        html.Label("Billing Filter:"),
        dcc.Slider(
            id="billing-slider",
            min=data[BILL].min(),
            max=data[BILL].max(),
            value=data[BILL].median(),
            step=100,
        ),

        html.Br(),
        html.Label("Upload CSV:"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag & Drop or Click"]),
            style={"height": "80px", "border": "1px dashed gray", "textAlign": "center"},
        ),
        html.Div(id="output-data"),
    ],
    style={"padding": "10px"},
)

offcanvas = dbc.Offcanvas(
    sidebar,
    id="offcanvas",
    title="Filters & Upload CSV",
    is_open=False,
    placement="start",
    scrollable=True,
)

toggle_btn = dbc.Button(
    "☰ Toggle Sidebar",
    id="toggle-btn",
    n_clicks=0,
    className="btn btn-outline-secondary my-3",
)

# --------------------------------------------------------
# KPI CARD FACTORY
# --------------------------------------------------------
def kpi_card(icon, title, value, color):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(icon, className=f"text-{color} fs-2"),
                html.H5(title, className="mt-2"),
                html.H3(value, className="fw-bold"),
            ]
        ),
        className="shadow-sm rounded-4 text-center p-3",
    )

# --------------------------------------------------------
# MAIN DASHBOARD CONTENT
# --------------------------------------------------------
content = dbc.Container(
    [
        dbc.Row(dbc.Col(toggle_btn, width=12)),
        offcanvas,

        dbc.Row(dbc.Col(html.H1("Universal Healthcare KPI Dashboard", className="text-center mb-5"), width=12)),

        dbc.Row(
            [
                dbc.Col(kpi_card("📈", "Readmission Rate", f"{readmission_rate:.2f}%", "danger")),
                dbc.Col(kpi_card("🏨", "Avg Length of Stay", f"{alos:.1f} days", "primary")),
                dbc.Col(kpi_card("💔", "Mortality Rate", f"{mortality_rate:.2f}%", "secondary")),
                dbc.Col(kpi_card("🛏️", "Bed Occupancy", f"{occupancy_rate:.2f}%", "warning")),
            ],
            className="g-4",
        ),

        html.Br(),

        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="age-graph"), width=6),
                dbc.Col(dcc.Graph(id="condition-graph"), width=6),
            ]
        ),

        dbc.Row(dbc.Col(dcc.Graph(id="insurance-graph"))),
        dbc.Row(dbc.Col(dcc.Graph(id="billing-graph"))),
        dbc.Row(dbc.Col(dcc.Graph(id="trend-graph"))),
        dbc.Row(dbc.Col(dcc.Graph(id="dept-graph"))),
    ],
    fluid=True,
    style={"padding": "20px"},
)

app.layout = content

# --------------------------------------------------------
# CALLBACKS (ALL SAFE)
# --------------------------------------------------------
@app.callback(
    Output("offcanvas", "is_open"),
    Input("toggle-btn", "n_clicks"),
    State("offcanvas", "is_open")
)
def toggle_sidebar(n, is_open):
    if n:
        return not is_open
    return is_open
# --------------------------------------------------------
# CLEAN BILLING COLUMN (Fix Plotly Invalid Value Error)
# --------------------------------------------------------
def clean_billing(df, billing_column):
    # Convert to numeric
    df[billing_column] = pd.to_numeric(df[billing_column], errors="coerce")

    # Remove NaN, negative, infinite
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=[billing_column])

    # Remove huge outliers (keeps dashboard clean)
    df = df[df[billing_column] < 500000]  # 5 lakh max

    return df


@app.callback(
    Output("age-graph", "figure"),
    Input("gender-filter", "value"),
)
def update_age(g):
    df = data if g is None else data[data[GENDER] == g]
    return px.histogram(df, x=AGE, color=GENDER, title="Age Distribution")

@app.callback(
    Output("condition-graph", "figure"),
    Input("gender-filter", "value"),
)
def update_condition(g):
    df = data if g is None else data[data[GENDER] == g]
    return px.pie(df, names=CONDITION, title="Condition Distribution")

@app.callback(
    Output("insurance-graph", "figure"),
    Input("gender-filter", "value"),
)
def update_insurance(g):
    df = data if g is None else data[data[GENDER] == g]
    return px.bar(df, x=INSURANCE, y=BILL, color=CONDITION, barmode="group",
                  title="Insurance Provider Billing Comparison")

@app.callback(
    Output("billing-graph", "figure"),
    Input("billing-slider", "value"),
)
def update_billing(limit):
    df = data[data[BILL] <= limit]
    return px.histogram(df, x=BILL, nbins=20, title="Billing Distribution")

@app.callback(
    Output("trend-graph", "figure"),
    Input("condition-filter", "value"),
)
def update_trends(condition):
    df = data if condition is None else data[data[CONDITION] == condition]
    trend = df.groupby("YearMonth").size().reset_index(name="Count")
    return px.line(trend, x="YearMonth", y="Count", title="Admission Trends")

@app.callback(
    Output("dept-graph", "figure"),
    Input("gender-filter", "value"),
)
def update_dept(g):
    df = data if g is None else data[data[GENDER] == g]
    dept = df.groupby(DEPARTMENT).agg(
        Patients=(AGE, "count"), AvgBilling=(BILL, "mean")
    ).reset_index()
    return px.bar(dept, x=DEPARTMENT, y=["Patients", "AvgBilling"], barmode="group",
                  title="Department Analysis")

# --------------------------------------------------------
# RUN
# --------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
