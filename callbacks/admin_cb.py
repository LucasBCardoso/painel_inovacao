"""
Admin callbacks — cross-project tasks panel
"""
from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from database import db, Project, ProjectTask, User
from callbacks.helpers import (
    icon, priority_badge, status_badge, trl_badge,
    user_avatar, progress_bar, trl_color, STATUS_LABELS,
)
from datetime import date


def register_admin(app):

    # Populate filter dropdowns
    @app.callback(
        Output("admin-project-filter", "data"),
        Output("admin-user-filter",    "data"),
        Input("url",     "pathname"),
        State("auth-store", "data"),
    )
    def populate_filters(pathname, user):
        if pathname != "/admin" or not user:
            raise PreventUpdate
        projects = Project.query.filter_by(is_active=True).order_by(Project.name).all()
        users    = User.query.filter_by(is_active=True).order_by(User.full_name).all()
        return (
            [{"value": str(p.id), "label": p.name} for p in projects],
            [{"value": str(u.id), "label": u.full_name} for u in users],
        )

    # Render tasks table
    @app.callback(
        Output("admin-tasks-content", "children"),
        Input("url",                   "pathname"),
        Input("admin-project-filter",  "value"),
        Input("admin-priority-filter", "value"),
        Input("admin-status-filter",   "value"),
        Input("admin-user-filter",     "value"),
        State("auth-store",            "data"),
    )
    def render_tasks(pathname, proj_filter, prio, status_f, user_filter, user):
        if pathname != "/admin" or not user:
            raise PreventUpdate

        query = ProjectTask.query.join(Project).filter(Project.is_active == True)

        if proj_filter:
            query = query.filter(ProjectTask.project_id.in_([int(x) for x in proj_filter]))
        if prio:
            query = query.filter(ProjectTask.priority == prio)

        tasks = query.order_by(ProjectTask.deadline).all()

        # Filter by status and user (Python-side)
        if status_f:
            tasks = [t for t in tasks if t.computed_status == status_f]
        if user_filter:
            uid_set = {int(x) for x in user_filter}
            tasks = [t for t in tasks if any(u.id in uid_set for u in t.assigned_users)]

        if not tasks:
            return dmc.Center(py="xl", children=dmc.Text("Nenhuma tarefa encontrada", c="dimmed"))

        today = date.today()

        rows = []
        for t in tasks:
            p     = Project.query.get(t.project_id)
            status = t.computed_status
            deadline_str = t.deadline.strftime("%d/%m/%Y") if t.deadline else "—"
            is_late      = t.is_delayed

            rows.append(html.Tr([
                html.Td(dmc.Group(gap="xs", children=[
                    trl_badge(p.trl if p else 1, 20),
                    dmc.Anchor(p.name if p else "—",
                               href=f"/projetos/{t.project_id}",
                               size="xs"),
                ])),
                html.Td(dmc.Text(t.title, size="sm", fw=500, lineClamp=2,
                                 style={"maxWidth": 260})),
                html.Td(priority_badge(t.priority)),
                html.Td(status_badge(status)),
                html.Td(dmc.Text(deadline_str, size="sm",
                                 c="red" if is_late else None, fw=700 if is_late else None)),
                html.Td(dmc.AvatarGroup(children=[
                    user_avatar(u.to_dict(), 22) for u in t.assigned_users[:3]
                ])),
                html.Td(dmc.Badge(
                    f"{int((today - t.deadline).days)}d" if is_late else "—",
                    color="red", variant="light", size="xs",
                ) if is_late else dmc.Text("—", size="xs", c="dimmed")),
            ]))

        # Summary header
        total    = len(tasks)
        delayed  = sum(1 for t in tasks if t.is_delayed)
        done     = sum(1 for t in tasks if t.computed_status == "completed")
        in_prog  = sum(1 for t in tasks if t.computed_status == "in_progress")

        summary = dmc.SimpleGrid(cols={"base": 2, "sm": 4}, spacing="sm", mb="md", children=[
            dmc.Paper(p="sm", radius="md",
                      style={"borderLeft": "4px solid #00afac"},
                      children=dmc.Stack(gap=0, children=[
                          dmc.Text(str(total), size="xl", fw=900),
                          dmc.Text("Total de Tarefas", size="xs", c="dimmed"),
                      ])),
            dmc.Paper(p="sm", radius="md",
                      style={"borderLeft": "4px solid #228be6"},
                      children=dmc.Stack(gap=0, children=[
                          dmc.Text(str(in_prog), size="xl", fw=900, c="blue"),
                          dmc.Text("Em Andamento", size="xs", c="dimmed"),
                      ])),
            dmc.Paper(p="sm", radius="md",
                      style={"borderLeft": "4px solid #2f9e44"},
                      children=dmc.Stack(gap=0, children=[
                          dmc.Text(str(done), size="xl", fw=900, c="green"),
                          dmc.Text("Concluídas", size="xs", c="dimmed"),
                      ])),
            dmc.Paper(p="sm", radius="md",
                      style={"borderLeft": "4px solid #fa5252"},
                      children=dmc.Stack(gap=0, children=[
                          dmc.Text(str(delayed), size="xl", fw=900, c="red"),
                          dmc.Text("Atrasadas", size="xs", c="dimmed"),
                      ])),
        ])

        table = dmc.Paper(
            p="md", radius="md",
            children=dmc.Table(
                striped=True, highlightOnHover=True,
                withTableBorder=True, withColumnBorders=True,
                children=[
                    html.Thead(html.Tr([
                        html.Th("Projeto"),
                        html.Th("Tarefa"),
                        html.Th("Prioridade"),
                        html.Th("Status"),
                        html.Th("Prazo"),
                        html.Th("Responsáveis"),
                        html.Th("Atraso"),
                    ])),
                    html.Tbody(rows),
                ],
            ),
        )

        return dmc.Stack(gap="md", children=[summary, table])
