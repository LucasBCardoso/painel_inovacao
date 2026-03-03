"""
Admin — painel cross-projetos de tarefas
"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon


def layout(user: dict):
    return dmc.Stack(gap="lg", children=[
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="sm", children=[
                icon("tabler:list-check", 24, "#00afac"),
                dmc.Title("Painel Admin", order=2, c="white"),
            ]),
        ]),

        # Filtros
        dmc.Group(gap="sm", wrap="wrap", children=[
            dmc.MultiSelect(
                id="admin-project-filter",
                placeholder="Projetos",
                data=[],  # preenchido por callback
                id="admin-project-filter",
                clearable=True, size="sm", style={"minWidth": 200},
            ),
            dmc.Select(
                id="admin-priority-filter",
                placeholder="Prioridade",
                data=[{"value":"alta","label":"Alta"},{"value":"media","label":"Média"},{"value":"baixa","label":"Baixa"}],
                clearable=True, size="sm", style={"width": 140},
            ),
            dmc.Select(
                id="admin-status-filter",
                placeholder="Status",
                data=[{"value":"pending","label":"Pendente"},
                      {"value":"in_progress","label":"Em Andamento"},
                      {"value":"completed","label":"Concluída"},
                      {"value":"delayed","label":"Atrasada"}],
                clearable=True, size="sm", style={"width": 160},
            ),
            dmc.MultiSelect(
                id="admin-user-filter",
                placeholder="Responsável",
                data=[],  # preenchido por callback
                clearable=True, size="sm", style={"minWidth": 200},
            ),
        ]),

        html.Div(id="admin-tasks-content"),
    ])
