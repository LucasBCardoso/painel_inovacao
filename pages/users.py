"""Usuários — grid de cards + CRUD"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon


def layout(user: dict):
    return dmc.Stack(gap="lg", children=[
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="sm", children=[
                icon("tabler:users", 24, "#00afac"),
                dmc.Title("Usuários", order=2, c="white"),
            ]),
            dmc.Button("Novo Usuário", id="user-new-btn",
                       leftSection=icon("tabler:user-plus", 16), size="sm",
                       style={"display": "block" if user.get("role") == "admin" else "none"}),
        ]),
        html.Div(id="users-grid"),
        dmc.Modal(id="user-modal", size="md", opened=False,
                  title=html.Div(id="user-modal-title"),
                  children=[html.Div(id="user-modal-body")]),
        dcc.Store(id="editing-user-id", data=None),
    ])
