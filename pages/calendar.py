"""Calendário — visão mensal de tarefas e reuniões"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon
from datetime import date


def layout(user: dict):
    today = date.today()
    return dmc.Stack(gap="lg", children=[
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="sm", children=[
                icon("tabler:calendar", 24, "#00afac"),
                dmc.Title("Calendário", order=2, c="white"),
            ]),
            dmc.Group(gap="sm", children=[
                dmc.ActionIcon(id="cal-prev", variant="subtle",
                               children=icon("tabler:chevron-left", 16)),
                html.Span(id="cal-title", style={"fontWeight": 600, "color": "#fff",
                                                  "fontSize": 15, "minWidth": 160,
                                                  "textAlign": "center"}),
                dmc.ActionIcon(id="cal-next", variant="subtle",
                               children=icon("tabler:chevron-right", 16)),
                dmc.Select(
                    id="cal-view",
                    value="month",
                    data=[{"value": "month", "label": "Mensal"},
                          {"value": "week",  "label": "Semanal"}],
                    size="xs", style={"width": 110},
                ),
            ]),
        ]),

        # Filters
        dmc.Group(gap="sm", wrap="wrap", children=[
            dmc.MultiSelect(
                id="cal-project-filter",
                placeholder="Projeto",
                data=[], clearable=True, size="sm", style={"minWidth": 200},
            ),
            dmc.MultiSelect(
                id="cal-user-filter",
                placeholder="Responsável",
                data=[], clearable=True, size="sm", style={"minWidth": 200},
            ),
            dmc.CheckboxGroup(
                id="cal-type-filter",
                value=["task", "meeting"],
                children=dmc.Group(gap="sm", children=[
                    dmc.Checkbox(label="Tarefas",  value="task"),
                    dmc.Checkbox(label="Reuniões", value="meeting"),
                ]),
            ),
        ]),

        dcc.Store(id="cal-month",  data=today.month),
        dcc.Store(id="cal-year",   data=today.year),
        html.Div(id="cal-grid"),
    ])
