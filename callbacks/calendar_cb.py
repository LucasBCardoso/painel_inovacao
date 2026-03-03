"""
Calendar callbacks — Painel TRL Delta
"""
import calendar
from datetime import date, timedelta
from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from database import db, Project, ProjectTask, Meeting, User
from callbacks.helpers import icon, trl_color, STATUS_COLORS

MONTHS_PT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]


def register_calendar(app):

    # Populate filter dropdowns
    @app.callback(
        Output("cal-project-filter", "data"),
        Output("cal-user-filter",    "data"),
        Input("url",       "pathname"),
        State("auth-store","data"),
    )
    def populate_cal_filters(pathname, user):
        if pathname != "/calendario" or not user:
            raise PreventUpdate
        projects = Project.query.filter_by(is_active=True).order_by(Project.name).all()
        users    = User.query.filter_by(is_active=True).order_by(User.full_name).all()
        return (
            [{"value": str(p.id), "label": p.name} for p in projects],
            [{"value": str(u.id), "label": u.full_name} for u in users],
        )

    # Navigate prev/next month
    @app.callback(
        Output("cal-month", "data"),
        Output("cal-year",  "data"),
        Input("cal-prev",   "n_clicks"),
        Input("cal-next",   "n_clicks"),
        State("cal-month",  "data"),
        State("cal-year",   "data"),
        prevent_initial_call=True,
    )
    def navigate_month(prev, nxt, month, year):
        from dash import ctx
        triggered = ctx.triggered_id
        if triggered == "cal-prev":
            m = month - 1
            y = year if m > 0 else year - 1
            m = m if m > 0 else 12
        else:
            m = month + 1
            y = year if m <= 12 else year + 1
            m = m if m <= 12 else 1
        return m, y

    # Render calendar
    @app.callback(
        Output("cal-title", "children"),
        Output("cal-grid",  "children"),
        Input("cal-month",           "data"),
        Input("cal-year",            "data"),
        Input("cal-project-filter",  "value"),
        Input("cal-user-filter",     "value"),
        Input("cal-type-filter",     "value"),
        State("auth-store",          "data"),
    )
    def render_calendar(month, year, proj_filter, user_filter, type_filter, user):
        if not user:
            raise PreventUpdate

        title = f"{MONTHS_PT[month-1]} {year}"
        today = date.today()
        type_filter = type_filter or ["task", "meeting"]

        # Collect events by date
        events_by_date: dict[date, list] = {}

        if "task" in type_filter:
            task_q = ProjectTask.query.join(Project).filter(Project.is_active == True)
            if proj_filter:
                task_q = task_q.filter(ProjectTask.project_id.in_([int(x) for x in proj_filter]))
            tasks = task_q.all()
            if user_filter:
                uid_set = {int(x) for x in user_filter}
                tasks = [t for t in tasks if any(u.id in uid_set for u in t.assigned_users)]

            for t in tasks:
                d = t.deadline
                if d and d.month == month and d.year == year:
                    events_by_date.setdefault(d, []).append({
                        "type": "task", "text": t.title[:26],
                        "color": STATUS_COLORS.get(t.computed_status, "gray"),
                        "is_delayed": t.is_delayed,
                    })

        if "meeting" in type_filter:
            meet_q = Meeting.query.join(Project).filter(Project.is_active == True)
            if proj_filter:
                meet_q = meet_q.filter(Meeting.project_id.in_([int(x) for x in proj_filter]))
            meetings = meet_q.all()

            for m in meetings:
                d = m.meeting_date
                if d and d.month == month and d.year == year:
                    events_by_date.setdefault(d, []).append({
                        "type": "meeting", "text": m.title[:26], "color": "violet",
                    })

        # Build calendar grid
        cal = calendar.monthcalendar(year, month)
        week_header = dmc.SimpleGrid(
            cols=7, spacing=2, mb=2,
            children=[dmc.Text(d, size="xs", fw=600, c="dimmed", ta="center")
                      for d in ["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"]],
        )

        rows = []
        for week in cal:
            cells = []
            for d in week:
                if d == 0:
                    cells.append(html.Div(style={"minHeight": 80, "background": "transparent"}))
                else:
                    this_date = date(year, month, d)
                    is_today  = this_date == today
                    evts      = events_by_date.get(this_date, [])

                    event_pills = []
                    for ev in evts[:3]:
                        color_map = {
                            "gray": "#5c5f66", "blue": "#228be6", "green": "#2f9e44",
                            "red": "#fa5252", "violet": "#7950f2", "orange": "#fd7e14",
                        }
                        bg = color_map.get(ev["color"], "#5c5f66")
                        event_pills.append(
                            dmc.Text(
                                ("📅 " if ev["type"] == "meeting" else "") + ev["text"],
                                size="xs",
                                style={
                                    "background": bg + "30",
                                    "color": bg,
                                    "borderRadius": 3,
                                    "padding": "1px 5px",
                                    "marginBottom": 2,
                                    "whiteSpace": "nowrap",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis",
                                    "display": "block",
                                    "fontSize": 10,
                                },
                            )
                        )
                    if len(evts) > 3:
                        event_pills.append(
                            dmc.Text(f"+{len(evts)-3} mais", size="xs", c="dimmed",
                                     style={"fontSize": 10})
                        )

                    cells.append(
                        html.Div(
                            style={
                                "minHeight": 80,
                                "background": "#25262b" if not is_today else "#00afac18",
                                "border": f"1px solid {'#00afac' if is_today else '#373A40'}",
                                "borderRadius": 6,
                                "padding": "4px 6px",
                            },
                            children=[
                                dmc.Text(
                                    str(d),
                                    size="xs", fw=700 if is_today else 400,
                                    c="teal" if is_today else "default",
                                    mb=2,
                                ),
                                *event_pills,
                            ],
                        )
                    )

            rows.append(dmc.SimpleGrid(cols=7, spacing=2, mb=2, children=cells))

        return title, dmc.Stack(gap=0, children=[week_header, *rows])
