"""
Dashboard — Visão Geral, Por Projeto, Por Usuário
"""
import dash_mantine_components as dmc
from dash import dcc, html
from callbacks.helpers import icon


def layout(user: dict):
    return dmc.Stack(gap="lg", children=[
        # ── Título ───────────────────────────────────────────────────────────
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="sm", children=[
                icon("tabler:dashboard", 24, "#00afac"),
                dmc.Title("Visão Geral", order=2, c="white"),
            ]),
            dmc.Button(
                "Atualizar",
                id="dashboard-refresh-btn",
                variant="subtle",
                size="sm",
                color="teal",
                leftSection=icon("tabler:refresh", 14),
            ),
        ]),

        # ── KPI cards ────────────────────────────────────────────────────────
        dmc.SimpleGrid(
            cols={"base": 2, "sm": 4},
            spacing="sm",
            children=[
                html.Div(id="kpi-total-projects"),
                html.Div(id="kpi-in-progress"),
                html.Div(id="kpi-delayed"),
                html.Div(id="kpi-avg-progress"),
            ],
        ),

        # ── Tabs ──────────────────────────────────────────────────────────────
        dmc.Tabs(
            id="dashboard-tabs",
            value="geral",
            children=[
                dmc.TabsList(children=[
                    dmc.TabsTab("Geral",        leftSection=icon("tabler:chart-pie", 14), value="geral"),
                    dmc.TabsTab("Por Projeto",   leftSection=icon("tabler:folder",   14), value="por-projeto"),
                    dmc.TabsTab("Por Usuário",   leftSection=icon("tabler:user",     14), value="por-usuario"),
                ]),
                # Tab Geral
                dmc.TabsPanel(value="geral", pt="md", children=[
                    dmc.SimpleGrid(
                        cols={"base": 1, "md": 2},
                        spacing="md",
                        children=[
                            dmc.Paper(
                                p="md", radius="md",
                                children=[
                                    dmc.Text("Projetos por TRL", fw=600, mb="sm"),
                                    dcc.Graph(id="chart-by-trl",
                                              config={"displayModeBar": False},
                                              style={"height": 260}),
                                ],
                            ),
                            dmc.Paper(
                                p="md", radius="md",
                                children=[
                                    dmc.Text("Distribuição por Prioridade", fw=600, mb="sm"),
                                    dcc.Graph(id="chart-by-priority",
                                              config={"displayModeBar": False},
                                              style={"height": 260}),
                                ],
                            ),
                            dmc.Paper(
                                p="md", radius="md",
                                children=[
                                    dmc.Text("Projetos por Setor", fw=600, mb="sm"),
                                    dcc.Graph(id="chart-by-sector",
                                              config={"displayModeBar": False},
                                              style={"height": 260}),
                                ],
                            ),
                            dmc.Paper(
                                p="md", radius="md",
                                children=[
                                    dmc.Text("Status de Progresso", fw=600, mb="sm"),
                                    dcc.Graph(id="chart-progress-status",
                                              config={"displayModeBar": False},
                                              style={"height": 260}),
                                ],
                            ),
                        ],
                    ),
                ]),

                # Tab Por Projeto
                dmc.TabsPanel(value="por-projeto", pt="md", children=[
                    dmc.Stack(gap="md", children=[
                        dmc.Paper(
                            p="md", radius="md",
                            children=[
                                dmc.Text("Gantt — Projetos (Start → Target)", fw=600, mb="sm"),
                                dcc.Graph(id="chart-projects-gantt",
                                          config={"displayModeBar": False},
                                          style={"height": 400}),
                            ],
                        ),
                        html.Div(id="projects-summary-table"),
                    ])
                ]),

                # Tab Por Usuário
                dmc.TabsPanel(value="por-usuario", pt="md", children=[
                    html.Div(id="users-metrics-grid"),
                ]),
            ],
        ),
    ])
