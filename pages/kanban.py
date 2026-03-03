"""
Kanban TRL — página de layout
Colunas: TRL 1..9 agrupadas por fase + colunas de Gate
"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon


PHASES = [
    {"label": "Descoberta",       "color": "violet", "trls": [1, 2, 3], "gate": "gate1"},
    {"label": "Desenvolvimento",  "color": "blue",   "trls": [4, 5, 6], "gate": "gate2"},
    {"label": "Industrialização", "color": "teal",   "trls": [7, 8, 9], "gate": None},
]


def layout(user: dict):
    return dmc.Stack(gap="lg", children=[
        # Header
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="sm", children=[
                icon("tabler:layout-kanban", 24, "#00afac"),
                dmc.Title("Kanban TRL", order=2, c="white"),
            ]),
            dmc.Group(gap="xs", children=[
                dmc.MultiSelect(
                    id="kanban-sector-filter",
                    placeholder="Filtrar por Setor",
                    data=["Software","Mecânica","Elétrica","Automação","Integração","Design","Processos"],
                    style={"width": 240},
                    clearable=True,
                    size="sm",
                ),
                dmc.Select(
                    id="kanban-priority-filter",
                    placeholder="Prioridade",
                    data=[{"value": "alta", "label": "Alta"},
                          {"value": "media","label": "Média"},
                          {"value": "baixa","label": "Baixa"}],
                    clearable=True,
                    size="sm",
                    style={"width": 140},
                ),
            ]),
        ]),

        # Modal de detalhe do projeto
        dmc.Modal(
            id="kanban-project-modal",
            size="xl",
            title=html.Div(id="kanban-modal-title"),
            opened=False,
            children=[html.Div(id="kanban-modal-body")],
        ),

        # Store para projeto selecionado no kanban
        dcc.Store(id="kanban-selected-project", data=None),

        # Board (renderizado por callback)
        html.Div(id="kanban-board"),
    ])
