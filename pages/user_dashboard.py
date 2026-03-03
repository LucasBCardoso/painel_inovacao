"""
User (personal) dashboard page layout — Painel TRL Delta
"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon


def layout(user: dict):
    return user_dashboard_layout()


def user_dashboard_layout():
    return dmc.Stack(
        gap="md",
        children=[
            # Header
            dmc.Group(
                gap="xs",
                children=[
                    icon("tabler:user-circle", size=26, color="#00afac"),
                    dmc.Title("Meu Painel", order=3, c="white"),
                ],
            ),

            # Welcome + KPIs
            html.Div(id="user-dash-kpis"),

            # Two-column layout
            dmc.Grid(
                gutter="md",
                children=[
                    # My pending tasks
                    dmc.GridCol(span={"base": 12, "md": 7}, children=[
                        dmc.Paper(
                            radius="md", p="md",
                            style={"background": "#25262b", "border": "1px solid #373A40"},
                            children=[
                                dmc.Group(justify="space-between", mb="sm", children=[
                                    dmc.Group(gap="xs", children=[
                                        icon("tabler:checklist", size=18, color="#00afac"),
                                        dmc.Text("Minhas Tarefas", fw=600, c="white"),
                                    ]),
                                    dmc.Select(
                                        id="user-dash-task-filter",
                                        data=[
                                            {"value": "all",        "label": "Todas"},
                                            {"value": "pending",    "label": "Pendentes"},
                                            {"value": "in_progress","label": "Em andamento"},
                                            {"value": "delayed",    "label": "Atrasadas"},
                                            {"value": "completed",  "label": "Concluídas"},
                                        ],
                                        value="all",
                                        size="xs",
                                        w=150,
                                    ),
                                ]),
                                html.Div(id="user-dash-tasks"),
                            ],
                        ),
                    ]),

                    # Right column — upcoming deadlines + my projects
                    dmc.GridCol(span={"base": 12, "md": 5}, children=[
                        dmc.Stack(gap="md", children=[
                            # Upcoming deadlines
                            dmc.Paper(
                                radius="md", p="md",
                                style={"background": "#25262b", "border": "1px solid #373A40"},
                                children=[
                                    dmc.Group(gap="xs", mb="sm", children=[
                                        icon("tabler:calendar-event", size=18, color="#00afac"),
                                        dmc.Text("Próximos prazos", fw=600, c="white"),
                                    ]),
                                    html.Div(id="user-dash-deadlines"),
                                ],
                            ),
                            # My projects
                            dmc.Paper(
                                radius="md", p="md",
                                style={"background": "#25262b", "border": "1px solid #373A40"},
                                children=[
                                    dmc.Group(gap="xs", mb="sm", children=[
                                        icon("tabler:folder", size=18, color="#00afac"),
                                        dmc.Text("Meus Projetos", fw=600, c="white"),
                                    ]),
                                    html.Div(id="user-dash-projects"),
                                ],
                            ),
                        ]),
                    ]),
                ],
            ),
        ],
    )
