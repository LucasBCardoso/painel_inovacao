"""
User dashboard callbacks — Painel TRL Delta
"""
from datetime import date, timedelta
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from database import db, User, Project, ProjectTask, TaskItem
from callbacks.helpers import icon, status_badge, priority_badge, trl_badge, progress_bar


def register_user_dashboard(app):

    @app.callback(
        Output("user-dash-kpis",      "children"),
        Output("user-dash-tasks",     "children"),
        Output("user-dash-deadlines", "children"),
        Output("user-dash-projects",  "children"),
        Input("url",                  "pathname"),
        Input("user-dash-task-filter","value"),
        State("auth-store",           "data"),
    )
    def render_user_dashboard(pathname, task_filter, user):
        if pathname != "/meu-painel" or not user:
            raise PreventUpdate

        db_user = User.query.get(user["id"]) if user else None
        if not db_user:
            raise PreventUpdate

        today = date.today()
        soon  = today + timedelta(days=7)

        # All tasks assigned to this user
        all_tasks = [t for t in db_user.tasks if t.project and t.project.is_active]

        # Filter
        filtered_tasks = all_tasks
        if task_filter and task_filter != "all":
            if task_filter == "delayed":
                filtered_tasks = [t for t in all_tasks if t.is_delayed]
            else:
                filtered_tasks = [t for t in all_tasks if t.computed_status == task_filter]

        # KPIs
        total_tasks    = len(all_tasks)
        done_tasks     = sum(1 for t in all_tasks if t.computed_status == "completed")
        delayed_tasks  = sum(1 for t in all_tasks if t.is_delayed)
        my_projects    = list({t.project for t in all_tasks})

        kpis = dmc.SimpleGrid(
            cols={"base": 2, "sm": 4}, spacing="md", mb="xs",
            children=[
                _kpi("Minhas tarefas",     total_tasks,   "tabler:checklist",       "teal"),
                _kpi("Concluídas",         done_tasks,    "tabler:circle-check",    "green"),
                _kpi("Atrasadas",          delayed_tasks, "tabler:alert-circle",    "red"),
                _kpi("Projetos",           len(my_projects), "tabler:folder",       "blue"),
            ],
        )

        # Task rows
        if not filtered_tasks:
            task_content = dmc.Text("Nenhuma tarefa encontrada.", c="dimmed", size="sm")
        else:
            rows = []
            for t in sorted(filtered_tasks, key=lambda x: (x.deadline or date.max)):
                deadline_str = t.deadline.strftime("%d/%m/%Y") if t.deadline else "—"
                color = "red" if t.is_delayed else ("green" if t.computed_status == "completed" else "dimmed")
                rows.append(
                    dmc.Paper(
                        radius="sm", p="sm", mb=4,
                        style={"background": "#1A1B1E", "border": "1px solid #373A40"},
                        children=[
                            dmc.Group(justify="space-between", children=[
                                dmc.Stack(gap=0, children=[
                                    dmc.Text(t.title, size="sm", fw=500, c="white"),
                                    dmc.Text(t.project.name if t.project else "", size="xs", c="dimmed"),
                                ]),
                                dmc.Group(gap="xs", children=[
                                    status_badge(t.computed_status),
                                    dmc.Text(deadline_str, size="xs", c=color),
                                ]),
                            ]),
                        ],
                    )
                )
            task_content = dmc.Stack(gap=0, children=rows)

        # Deadlines
        upcoming = [t for t in all_tasks if t.deadline and today <= t.deadline <= soon and t.computed_status != "completed"]
        upcoming.sort(key=lambda x: x.deadline)

        if not upcoming:
            deadlines_content = dmc.Text("Sem prazos próximos.", c="dimmed", size="sm")
        else:
            dl_items = []
            for t in upcoming[:8]:
                days_left = (t.deadline - today).days
                color = "red" if days_left <= 2 else "orange" if days_left <= 4 else "teal"
                dl_items.append(
                    dmc.Group(
                        justify="space-between", mb=4,
                        children=[
                            dmc.Text(t.title[:30], size="sm", c="white"),
                            dmc.Badge(f"{days_left}d", color=color, variant="light", size="sm"),
                        ],
                    )
                )
            deadlines_content = dmc.Stack(gap=0, children=dl_items)

        # My projects
        if not my_projects:
            projects_content = dmc.Text("Sem projetos atribuídos.", c="dimmed", size="sm")
        else:
            proj_items = []
            for pr in sorted(my_projects, key=lambda x: -x.progress):
                proj_items.append(
                    dmc.Group(
                        justify="space-between", mb="xs",
                        children=[
                            dmc.Group(gap="xs", children=[
                                trl_badge(pr.trl_level, size="xs"),
                                dmc.Text(pr.name[:25], size="sm", c="white"),
                            ]),
                            dmc.Text(f"{pr.progress}%", size="sm", c="teal", fw=600),
                        ],
                    )
                )
            projects_content = dmc.Stack(gap=0, children=proj_items)

        return kpis, task_content, deadlines_content, projects_content


def _kpi(label: str, value, icon_name: str, color: str):
    return dmc.Paper(
        radius="md", p="sm",
        style={"background": "#25262b", "border": "1px solid #373A40"},
        children=[
            dmc.Group(gap="xs", mb=2, children=[
                icon(icon_name, size=18, color=f"var(--mantine-color-{color}-5)"),
                dmc.Text(label, size="xs", c="dimmed"),
            ]),
            dmc.Title(str(value), order=3,
                      style={"color": f"var(--mantine-color-{color}-5)"}),
        ],
    )
