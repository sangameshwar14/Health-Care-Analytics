import dash
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, html, State, ctx
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
import numpy as np
from datetime import datetime, timedelta
import io

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
# DATA PROCESSING UTILITIES
# --------------------------------------------------------
def process_data(df):
    if df.empty:
        return df, None, None, None, None, None, None, None

    # Autodetect columns
    age_col = auto_detect_column(df, ["age", "patientage", "years"])
    gender_col = auto_detect_column(df, ["gender", "sex"])
    billing_col = auto_detect_column(df, ["billingamount", "bill", "charge", "amount"])
    date_col = auto_detect_column(df, ["dateofadmission", "admissiondate", "date"])
    condition_col = auto_detect_column(df, ["medicalcondition", "diagnosis", "condition"])
    insurance_col = auto_detect_column(df, ["insuranceprovider", "insurance", "payer"])
    department_col = auto_detect_column(df, ["department", "unit", "ward"])

    # Fallbacks and cleanup
    if age_col is None:
        df["Age"] = np.random.randint(18, 90, size=len(df))
        age_col = "Age"
    if gender_col is None:
        df["Gender"] = np.random.choice(["Male", "Female"], size=len(df))
        gender_col = "Gender"
    if billing_col is None:
        df["Billing Amount"] = np.random.randint(500, 20000, size=len(df))
        billing_col = "Billing Amount"
    df[billing_col] = pd.to_numeric(df[billing_col], errors="coerce").fillna(0)

    if date_col is None:
        df["Date of Admission"] = pd.date_range(start="2023-01-01", periods=len(df), freq="D")
        date_col = "Date of Admission"
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["YearMonth"] = df[date_col].dt.to_period("M").astype(str)

    if condition_col is None:
        df["Medical Condition"] = np.random.choice(["Diabetes", "Hypertension", "Cancer", "Asthma"], size=len(df))
        condition_col = "Medical Condition"
    if insurance_col is None:
        df["Insurance Provider"] = np.random.choice(["Aetna", "BlueCross", "UnitedHealth", "Medicaid"], size=len(df))
        insurance_col = "Insurance Provider"
    if department_col is None:
        df["Department"] = np.random.choice(["Cardiology", "Neurology", "Oncology", "Orthopedics"], size=len(df))
        department_col = "Department"

    # Metrics
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

# Initial data load for structure
initial_df = pd.read_csv("assets/healthcare.csv")
processed_df, AGE, GENDER, BILL, DATE, CONDITION, INSURANCE, DEPARTMENT = process_data(initial_df)

# --------------------------------------------------------
# App Initialization
# --------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap"
    ],
    suppress_callback_exceptions=True
)
app.title = "Healthcare Analytics Dashboard"

# --------------------------------------------------------
# UI COMPONENTS
# --------------------------------------------------------

def create_header():
    return html.Div(
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Healthcare Analytics Dashboard", className="header-title"),
                        html.P("Built using Python, Dash, Plotly | Real-time Insights Platform", className="header-subtitle mb-0"),
                        html.Small(id="header-clock", className="text-muted"),
                    ],
                    md=7
                ),
                dbc.Col(
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="fa-solid fa-download me-2"), "Export"],
                                id="export-btn",
                                className="btn-primary rounded-pill px-3 me-2"
                            ),
                            dbc.Button(
                                [html.I(className="fa-solid fa-bars me-2"), "Filters"],
                                id="toggle-btn",
                                className="btn-primary rounded-pill px-3 me-2"
                            ),
                            html.Div(
                                [
                                    html.I(className="fa-solid fa-moon theme-toggle", id="theme-toggle-btn"),
                                ],
                                className="d-flex align-items-center ms-2"
                            ),
                            html.I(className="fa-solid fa-circle-user fs-3 text-primary ms-3", style={"cursor": "pointer"}),
                        ],
                        className="d-flex align-items-center justify-content-end h-100"
                    ),
                    md=5
                )
            ],
            className="align-items-center"
        ),
        className="header-container mb-4",
        id="dashboard-header"
    )

def kpi_card(id, icon, title, value, color_class, border_color):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(html.I(className=f"{icon} kpi-icon text-{color_class}"), className="mb-2"),
                html.P(title, className="kpi-label mb-1"),
                html.H3(value, id=id, className="kpi-value"),
                html.Div(className="mt-2", style={"height": "4px", "width": "40px", "backgroundColor": border_color, "borderRadius": "2px"})
            ]
        ),
        className="custom-card kpi-card h-100",
        style={"borderLeft": f"5px solid {border_color}"}
    )

def create_sidebar():
    return dbc.Offcanvas(
        html.Div(
            [
                html.Div(
                    [
                        html.I(className="fa-solid fa-filter me-2 text-primary"),
                        html.H4("Global Filters", className="d-inline"),
                    ],
                    className="mb-4"
                ),
                html.Hr(),
                
                html.Label([html.I(className="fa-solid fa-calendar-days me-2"), "Date Range"], className="filter-label"),
                dcc.DatePickerRange(
                    id="date-picker",
                    min_date_allowed=datetime(2018, 1, 1),
                    max_date_allowed=datetime.now() + timedelta(days=365),
                    start_date=datetime(2019, 1, 1).date(),
                    end_date=datetime.now().date(),
                    className="mb-3 w-100"
                ),

                html.Label([html.I(className="fa-solid fa-venus-mars me-2"), "Gender"], className="filter-label"),
                dcc.Dropdown(
                    id="gender-filter",
                    options=[{"label": g, "value": g} for g in processed_df[GENDER].unique()],
                    placeholder="All Genders",
                    className="mb-3"
                ),

                html.Label([html.I(className="fa-solid fa-stethoscope me-2"), "Medical Condition"], className="filter-label"),
                dcc.Dropdown(
                    id="condition-filter",
                    options=[{"label": c, "value": c} for c in processed_df[CONDITION].unique()],
                    placeholder="All Conditions",
                    className="mb-3"
                ),

                html.Label([html.I(className="fa-solid fa-file-invoice-dollar me-2"), "Max Billing"], className="filter-label"),
                dcc.Slider(
                    min=0,
                    max=processed_df[BILL].max() if not processed_df.empty else 100000,
                    value=processed_df[BILL].max() if not processed_df.empty else 100000,
                    id="billing-slider-id", # Fixed ID conflict if any
                    className="mb-4"
                ),

                html.Hr(),
                html.Label([html.I(className="fa-solid fa-cloud-arrow-up me-2"), "Data Source"], className="filter-label"),
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(["Drag & Drop or ", html.A("Select File", className="text-primary")]),
                    style={
                        "width": "100%", "height": "70px", "lineHeight": "70px",
                        "borderWidth": "1px", "borderStyle": "dashed",
                        "borderRadius": "8px", "textAlign": "center", "backgroundColor": "rgba(0,0,0,0.02)"
                    }
                ),
                html.Div(id="upload-status", className="mt-2 small text-success"),
                
                dbc.Button("Reset All Filters", id="reset-filters-btn", color="link", className="mt-4 text-primary p-0")
            ],
            className="sidebar-content"
        ),
        id="offcanvas",
        title=None,
        is_open=False,
        placement="start",
        className="w-auto"
    )

def create_chart_card(title, icon, graph_id, width=12):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(className=f"{icon} text-primary me-2"),
                            html.Span(title, className="chart-title d-inline"),
                        ],
                        className="d-flex align-items-center mb-3"
                    ),
                    dcc.Loading(
                        dcc.Graph(id=graph_id, config={"displayModeBar": False}, style={"height": "300px"}),
                        type="circle",
                        color="#0061ff"
                    )
                ]
            ),
            className="custom-card h-100"
        ),
        md=width,
        className="mb-4"
    )

# --------------------------------------------------------
# Layout
# --------------------------------------------------------
app.layout = html.Div(
    [
        dcc.Store(id="data-store", data=processed_df.to_dict("records")),
        dcc.Store(id="theme-store", data="light"),
        dcc.Store(id="drill-down-store", data={}),
        dcc.Download(id="download-dataframe-csv"),
        dcc.Interval(id="clock-interval", interval=1000, n_intervals=0),
        
        create_header(),
        create_sidebar(),
        
        dbc.Container(
            [
                # KPI Row
                dbc.Row(
                    [
                        dbc.Col(kpi_card("kpi-total-patients", "fa-solid fa-users", "Total Patients", "--", "primary", "#0061ff"), md=4, lg=2),
                        dbc.Col(kpi_card("kpi-avg-billing", "fa-solid fa-receipt", "Avg Billing", "--", "success", "#20c997"), md=4, lg=2),
                        dbc.Col(kpi_card("kpi-readmission", "fa-solid fa-rotate-left", "Readmission", "--", "danger", "#ff4757"), md=4, lg=2),
                        dbc.Col(kpi_card("kpi-avg-stay", "fa-solid fa-bed", "Avg Stay", "--", "info", "#1e90ff"), md=4, lg=2),
                        dbc.Col(kpi_card("kpi-mortality", "fa-solid fa-skull-crossbones", "Mortality", "--", "secondary", "#747d8c"), md=4, lg=2),
                        dbc.Col(kpi_card("kpi-occupancy", "fa-solid fa-hospital", "Bed Occupancy", "--", "warning", "#ffa502"), md=4, lg=2),
                    ],
                    className="g-4 mb-4 fade-in"
                ),

                # Dynamic Insights Section
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.I(className="fa-solid fa-wand-magic-sparkles text-accent me-2"),
                                            html.H5("Business Insights / Key Findings", className="d-inline fw-bold"),
                                        ],
                                        className="mb-2"
                                    ),
                                    html.Div(id="dynamic-insights-content", className="mt-3")
                                ]
                            ),
                            className="custom-card mb-4 border-accent",
                            style={"borderTop": "3px solid var(--accent)"}
                        )
                    )
                ),

                # Charts Sections
                dbc.Row([
                    create_chart_card("Age Distribution by Gender", "fa-solid fa-people-group", "age-graph", 7),
                    create_chart_card("Gender Distribution", "fa-solid fa-chart-pie", "gender-pie", 5),
                ], className="fade-in"),

                dbc.Row([
                    create_chart_card("Billing Amount Distribution", "fa-solid fa-money-bill-trend-up", "billing-graph", 6),
                    create_chart_card("Insurance Provider Comparison", "fa-solid fa-building-shield", "insurance-graph", 6),
                ], className="fade-in"),

                dbc.Row([
                    create_chart_card("Admission Trends", "fa-solid fa-chart-line", "trend-graph", 8),
                    create_chart_card("Patient Journey Funnel", "fa-solid fa-filter-circle-dollar", "funnel-graph", 4),
                ], className="fade-in"),

                dbc.Row([
                    create_chart_card("Department Performance", "fa-solid fa-hospital-user", "dept-graph", 7),
                    create_chart_card("Cost Breakdown Waterfall", "fa-solid fa-water", "waterfall-graph", 5),
                ], className="fade-in mb-5"),
            ],
            fluid=True,
            className="px-4"
        ),
    ],
    id="main-app-container",
    className="bg-light min-vh-100 transition-all"
)

# --------------------------------------------------------
# CALLBACKS
# --------------------------------------------------------

# 1. Update Clock
@app.callback(Output("header-clock", "children"), Input("clock-interval", "n_intervals"))
def update_clock(n):
    return datetime.now().strftime("%d %b %Y | %H:%M:%S")

# 2. Toggle Sidebar
@app.callback(Output("offcanvas", "is_open"), Input("toggle-btn", "n_clicks"), State("offcanvas", "is_open"))
def toggle_sidebar(n, is_open):
    if n: return not is_open
    return is_open

# 3. Theme Toggle
@app.callback(
    [Output("main-app-container", "className"), Output("theme-store", "data"), Output("theme-toggle-btn", "className")],
    Input("theme-toggle-btn", "n_clicks"),
    State("theme-store", "data")
)
def toggle_theme(n, current_theme):
    if n is None: return "bg-light min-vh-100", "light", "fa-solid fa-moon theme-toggle"
    new_theme = "dark" if current_theme == "light" else "light"
    container_class = "bg-light min-vh-100 dark-mode" if new_theme == "dark" else "bg-light min-vh-100"
    icon_class = "fa-solid fa-sun theme-toggle" if new_theme == "dark" else "fa-solid fa-moon theme-toggle"
    return container_class, new_theme, icon_class

# 4. Data Handling (Upload)
@app.callback(
    [Output("data-store", "data"), Output("upload-status", "children"), Output("billing-slider-id", "max"), Output("billing-slider-id", "value")],
    Input("upload-data", "contents"),
    State("upload-data", "filename")
)
def handle_upload(contents, filename):
    if contents is None:
        # Check if assets/healthcare.csv exists as default
        try:
            df = pd.read_csv("assets/healthcare.csv")
            processed, _, _, _, _, _, _, _ = process_data(df)
            return processed.to_dict("records"), "Default data loaded.", processed[BILL].max(), processed[BILL].max()
        except:
            return [], "", 100000, 100000

    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    processed, _, _, _, _, _, _, _ = process_data(df)
    return processed.to_dict("records"), f"✅ {filename} loaded.", processed[BILL].max(), processed[BILL].max()

# 5. Drill-Down Manager
@app.callback(
    Output("drill-down-store", "data"),
    [
        Input("dept-graph", "clickData"),
        Input("insurance-graph", "clickData"),
        Input("gender-pie", "clickData"),
        Input("reset-filters-btn", "n_clicks")
    ],
    State("drill-down-store", "data")
)
def update_drill_down(dept_click, ins_click, gender_click, reset_n, current_drill_down):
    triggered = ctx.triggered_id
    if triggered == "reset-filters-btn": return {}
    
    current = {}
    if dept_click: current["Department"] = dept_click["points"][0]["x"]
    if ins_click: current["Insurance Provider"] = ins_click["points"][0]["x"]
    if gender_click: current["Gender"] = gender_click["points"][0]["label"]
    
    return current

# 6. Global Filtered Data Logic
def get_filtered_df(data_dict, start_date, end_date, gender, condition, bill_max, drill_down):
    if not data_dict: return pd.DataFrame()
    df = pd.DataFrame(data_dict)
    df[DATE] = pd.to_datetime(df[DATE])
    
    mask = (df[DATE] >= start_date) & (df[DATE] <= end_date)
    if gender: mask &= (df[GENDER] == gender)
    if condition: mask &= (df[CONDITION] == condition)
    if bill_max: mask &= (df[BILL] <= bill_max)
    
    for col, val in drill_down.items():
        if col in df.columns:
            mask &= (df[col] == val)
            
    return df[mask]

# 7. Update All Charts and KPIs
@app.callback(
    [
        Output("kpi-total-patients", "children"), Output("kpi-avg-billing", "children"),
        Output("kpi-readmission", "children"), Output("kpi-avg-stay", "children"),
        Output("kpi-mortality", "children"), Output("kpi-occupancy", "children"),
        Output("dynamic-insights-content", "children"),
        Output("age-graph", "figure"), Output("gender-pie", "figure"),
        Output("billing-graph", "figure"), Output("insurance-graph", "figure"),
        Output("trend-graph", "figure"), Output("funnel-graph", "figure"),
        Output("dept-graph", "figure"), Output("waterfall-graph", "figure"),
    ],
    [
        Input("data-store", "data"),
        Input("date-picker", "start_date"), Input("date-picker", "end_date"),
        Input("gender-filter", "value"), Input("condition-filter", "value"),
        Input("billing-slider-id", "value"),
        Input("drill-down-store", "data"),
        Input("theme-store", "data")
    ]
)
def update_dashboard(data_dict, start, end, gender, condition, bill_max, drill_down, theme):
    df = get_filtered_df(data_dict, start, end, gender, condition, bill_max, drill_down)
    template = "plotly_dark" if theme == "dark" else "plotly_white"
    
    def apply_style(fig):
        fig.update_layout(
            template=template,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        return fig

    if df.empty:
        empty_fig = apply_style(px.scatter(title="No data matching filters"))
        return ["0"]*6 + [html.P("No insights", className="text-muted")] + [empty_fig]*8

    # KPIs
    kpis = [
        f"{len(df):,}",
        f"${df[BILL].mean():,.0f}",
        f"{(df['Readmitted'].mean()*100):.1f}%",
        f"{df['Length of Stay'].mean():.1f}d",
        f"{((df['Outcome'] == 'Deceased').mean()*100):.1f}%",
        f"{((df['Beds Occupied'].mean() / df['Total Beds'].mean()) * 100):.1f}%"
    ]

    # Insights Logic
    insights = []
    
    # 1. Top Revenue Dept
    top_dept = df.groupby(DEPARTMENT)[BILL].sum().idxmax()
    insights.append(html.Li([html.I(className="fa-solid fa-trophy me-2 text-warning"), f"Highest revenue generated by ", html.B(top_dept)]))
    
    # 2. Readmission Analysis
    readmit_rate = df["Readmitted"].mean() * 100
    status = "Exceeds" if readmit_rate > 20 else "Within"
    color = "text-danger" if readmit_rate > 20 else "text-success"
    insights.append(html.Li([html.I(className="fa-solid fa-triangle-exclamation me-2 " + color), f"Readmission rate is ", html.B(f"{readmit_rate:.1f}%"), f" ({status} 20% benchmark)"]))

    # 3. Admission Trends (MoM)
    trend_df = df.groupby("YearMonth").size()
    if len(trend_df) >= 2:
        change = ((trend_df.iloc[-1] - trend_df.iloc[-2]) / trend_df.iloc[-2]) * 100
        trend_icon = "fa-solid fa-arrow-trend-up text-danger" if change > 0 else "fa-solid fa-arrow-trend-down text-success"
        insights.append(html.Li([html.I(className=trend_icon + " me-2"), f"Admissions showed a ", html.B(f"{abs(change):.1f}% {'increase' if change > 0 else 'decrease'}"), " vs last month."]))

    # 4. Most Common Condition
    top_cond = df[CONDITION].value_counts().idxmax()
    insights.append(html.Li([html.I(className="fa-solid fa-disease me-2 text-primary"), f"Primary condition observed: ", html.B(top_cond)]))

    insight_list = html.Ul(insights, className="list-unstyled mb-0")

    # Figures
    fig_age = apply_style(px.histogram(df, x=AGE, color=GENDER, barmode="overlay", color_discrete_sequence=["#0061ff", "#60e5cf"]))
    fig_gender = apply_style(px.pie(df, names=GENDER, hole=0.6, color_discrete_sequence=["#0061ff", "#60e5cf"]))
    fig_bill = apply_style(px.histogram(df, x=BILL, nbins=30, color_discrete_sequence=["#20c997"]))
    fig_ins = apply_style(px.bar(df.groupby([INSURANCE, CONDITION])[BILL].mean().reset_index(), x=INSURANCE, y=BILL, color=CONDITION, barmode="group"))
    
    trend_df = df.groupby("YearMonth").size().reset_index(name="Count")
    fig_trend = apply_style(px.line(trend_df, x="YearMonth", y="Count", markers=True))
    fig_trend.update_traces(line_shape="spline")
    
    fig_funnel = apply_style(go.Figure(go.Funnel(y=["Admissions", "Treatments", "Discharges", "Readmitted"], x=[len(df), int(len(df)*0.9), int(len(df)*0.85), df['Readmitted'].sum()])))
    
    dept_df = df.groupby(DEPARTMENT).agg(Patients=(AGE, "count"), AvgBill=(BILL, "mean")).reset_index()
    fig_dept = apply_style(px.bar(dept_df, x=DEPARTMENT, y=["Patients", "AvgBill"], barmode="group"))
    
    fig_water = apply_style(go.Figure(go.Waterfall(x=dept_df[DEPARTMENT], y=dept_df["AvgBill"])))

    return *kpis, insight_list, fig_age, fig_gender, fig_bill, fig_ins, fig_trend, fig_funnel, fig_dept, fig_water

# 8. Export Data
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-btn", "n_clicks"),
    [
        State("data-store", "data"),
        State("date-picker", "start_date"), State("date-picker", "end_date"),
        State("gender-filter", "value"), State("condition-filter", "value"),
        State("billing-slider-id", "value"), State("drill-down-store", "data")
    ],
    prevent_initial_call=True
)
def export_csv(n, data_dict, start, end, gender, condition, bill, drill):
    df = get_filtered_df(data_dict, start, end, gender, condition, bill, drill)
    return dcc.send_data_frame(df.to_csv, f"healthcare_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

# 9. Reset Filters (Clear dropdowns)
@app.callback(
    [Output("gender-filter", "value"), Output("condition-filter", "value"), Output("date-picker", "start_date"), Output("date-picker", "end_date")],
    Input("reset-filters-btn", "n_clicks")
)
def reset_ui_filters(n):
    if n:
        return None, None, datetime(2019, 1, 1).date(), datetime.now().date()
    return dash.no_update

# --------------------------------------------------------
# RUN
# --------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
