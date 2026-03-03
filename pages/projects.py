"""
Projetos — lista agrupada por TRL com busca e filtros
"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon


def layout(user: dict):
    return dmc.Stack(gap="lg", children=[
        # Header
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="sm", children=[
                icon("tabler:folder", 24, "#00afac"),
                dmc.Title("Projetos", order=2, c="white"),
            ]),
            dmc.Button(
                "Novo Projeto",
                id="new-project-btn",
                leftSection=icon("tabler:plus", 16),
                size="sm",
            ) if user.get("role") == "admin" else html.Span(),
        ]),

        # Filtros
        dmc.Group(gap="sm", children=[
            dmc.TextInput(
                id="projects-search",
                placeholder="Buscar projeto…",
                leftSection=icon("tabler:search", 16),
                style={"maxWidth": 320},
                debounce=300,
                size="sm",
            ),
            dmc.MultiSelect(
                id="projects-sector-filter",
                placeholder="Setor",
                data=["Software","Mecânica","Elétrica","Automação","Integração","Design","Processos"],
                clearable=True, size="sm", style={"width": 200},
            ),
            dmc.Select(
                id="projects-priority-filter",
                placeholder="Prioridade",
                data=[{"value":"alta","label":"Alta"},
                      {"value":"media","label":"Média"},
                      {"value":"baixa","label":"Baixa"}],
                clearable=True, size="sm", style={"width": 140},
            ),
            dmc.Select(
                id="projects-trl-filter",
                placeholder="TRL",
                data=[{"value": str(i), "label": f"TRL {i}"} for i in range(1, 10)],
                clearable=True, size="sm", style={"width": 110},
            ),
        ]),

        # Modals
        dmc.Modal(
            id="new-project-modal",
            title=dmc.Group(gap="sm", children=[
                icon("tabler:plus", 20, "#00afac"),
                dmc.Text("Novo Projeto", fw=700),
            ]),
            size="xl",
            opened=False,
            children=[html.Div(id="new-project-form-body")],
        ),

        # Board de projetos (renderizado por callback)
        dcc.Store(id="projects-list-trigger", data=0),
        html.Div(id="projects-list"),
    ])
