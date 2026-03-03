"""
Report page layout — Painel TRL Delta
"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon


def layout(user: dict):
    return report_layout()


def report_layout():
    return dmc.Stack(
        gap="md",
        children=[
            # Header
            dmc.Group(
                justify="space-between",
                align="center",
                children=[
                    dmc.Group(
                        gap="xs",
                        children=[
                            icon("tabler:clipboard-text", size=26, color="#00afac"),
                            dmc.Title("Relatório de Projeto", order=3, c="white"),
                        ],
                    ),
                    dmc.Button(
                        "Imprimir / Exportar",
                        id="report-print-btn",
                        leftSection=icon("tabler:printer", size=16),
                        color="teal",
                        variant="light",
                    ),
                ],
            ),

            # Filters
            dmc.Paper(
                radius="md", p="md",
                style={"background": "#25262b", "border": "1px solid #373A40"},
                children=[
                    dmc.Grid(
                        gutter="md",
                        children=[
                            dmc.GridCol(span={"base": 12, "md": 5}, children=[
                                dmc.Select(
                                    id="report-project-select",
                                    label="Projeto",
                                    placeholder="Selecione um projeto…",
                                    data=[],
                                    clearable=True,
                                    searchable=True,
                                    leftSection=icon("tabler:folder", size=16),
                                ),
                            ]),
                            dmc.GridCol(span={"base": 12, "md": 3}, children=[
                                dmc.DatePickerInput(
                                    id="report-date-from",
                                    label="A partir de",
                                    placeholder="Data inicial",
                                    clearable=True,
                                ),
                            ]),
                            dmc.GridCol(span={"base": 12, "md": 3}, children=[
                                dmc.DatePickerInput(
                                    id="report-date-to",
                                    label="Até",
                                    placeholder="Data final",
                                    clearable=True,
                                ),
                            ]),
                            dmc.GridCol(span={"base": 12, "md": 1}, children=[
                                dmc.Button(
                                    "Gerar",
                                    id="report-gen-btn",
                                    color="teal",
                                    fullWidth=True,
                                    mt=22,
                                ),
                            ]),
                        ],
                    ),
                ],
            ),

            # Report content area
            html.Div(id="report-content"),
        ],
    )
