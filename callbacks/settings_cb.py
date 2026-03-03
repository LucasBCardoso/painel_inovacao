"""
Settings callbacks — Painel TRL Delta
"""
from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from database import db, SystemConfig
from callbacks.helpers import icon

TRL_DESCRIPTIONS = {
    1: "Princípios básicos observados e reportados. Conceitos iniciais identificados.",
    2: "Conceito de tecnologia formulado e/ou aplicação, sem prova experimental.",
    3: "Prova de conceito experimental. Componentes principais testados em lab.",
    4: "Componentes e/ou breadboard validados em laboratório (bancada).",
    5: "Componentes validados em ambiente relevante (industrialmente relevante).",
    6: "Sistema/subsistema ou protótipo demonstrado em ambiente relevante.",
    7: "Protótipo demonstrado em ambiente operacional.",
    8: "Sistema completo e qualificado. Produção-piloto estabelecida.",
    9: "Sistema real comprovado em ambiente operacional (fabricação competitiva).",
}


def register_settings(app):

    # Load tags on page enter
    @app.callback(
        Output("settings-tags-input", "value"),
        Input("url", "pathname"),
        State("auth-store", "data"),
    )
    def load_tags(pathname, user):
        if pathname != "/configuracoes" or not user:
            raise PreventUpdate
        cfg = SystemConfig.query.filter_by(key="system_tags").first()
        if cfg and cfg.value:
            return [t.strip() for t in cfg.value.split(",") if t.strip()]
        return []

    # Save tags
    @app.callback(
        Output("settings-tags-feedback", "children"),
        Input("settings-tags-save-btn", "n_clicks"),
        State("settings-tags-input",   "value"),
        State("auth-store",            "data"),
        prevent_initial_call=True,
    )
    def save_tags(n, tags, user):
        if not n or not user or user.get("role") != "admin":
            raise PreventUpdate
        cfg = SystemConfig.query.filter_by(key="system_tags").first()
        if not cfg:
            cfg = SystemConfig(key="system_tags", value="")
            db.session.add(cfg)
        cfg.value = ",".join(tags or [])
        db.session.commit()
        return dmc.Alert("Tags salvas com sucesso!", color="green", variant="light")

    # Load TRL docs
    @app.callback(
        Output("settings-trl-docs", "children"),
        Input("url", "pathname"),
        State("auth-store", "data"),
    )
    def load_trl_docs(pathname, user):
        if pathname != "/configuracoes" or not user:
            raise PreventUpdate
        rows = []
        for trl, desc in TRL_DESCRIPTIONS.items():
            color = ["red","red","red","orange","orange","orange","teal","teal","teal"][trl - 1]
            rows.append(
                dmc.Group(
                    gap="sm", mb="sm", align="flex-start",
                    children=[
                        dmc.Badge(f"TRL {trl}", color=color, variant="filled", size="lg",
                                  style={"minWidth": 60, "justifyContent": "center"}),
                        dmc.Text(desc, size="sm", c="dimmed", style={"flex": 1}),
                    ],
                )
            )
        return dmc.Stack(gap=2, children=rows)
