"""
Settings page layout — Painel TRL Delta
"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon


def layout(user: dict):
    return settings_layout()


def settings_layout():
    return dmc.Stack(
        gap="md",
        children=[
            # Header
            dmc.Group(
                gap="xs",
                children=[
                    icon("tabler:settings", size=26, color="#00afac"),
                    dmc.Title("Configurações", order=3, c="white"),
                ],
            ),

            dmc.Tabs(
                value="tags",
                children=[
                    dmc.TabsList(children=[
                        dmc.TabsTab("Tags do Sistema",   value="tags",    leftSection=icon("tabler:tag", size=14)),
                        dmc.TabsTab("Documentação TRL",  value="trl-docs",leftSection=icon("tabler:book", size=14)),
                        dmc.TabsTab("Preferências",       value="prefs",   leftSection=icon("tabler:adjustments", size=14)),
                    ]),

                    # ── Tags ─────────────────────────────────────────
                    dmc.TabsPanel(value="tags", pt="md", children=[
                        dmc.Paper(
                            radius="md", p="md",
                            style={"background": "#25262b", "border": "1px solid #373A40"},
                            children=[
                                dmc.Group(justify="space-between", mb="md", children=[
                                    dmc.Text("Tags disponíveis para projetos", fw=600, c="white"),
                                    dmc.Button(
                                        "Salvar",
                                        id="settings-tags-save-btn",
                                        color="teal",
                                        leftSection=icon("tabler:device-floppy", size=15),
                                    ),
                                ]),
                                dmc.TagsInput(
                                    id="settings-tags-input",
                                    label="Tags",
                                    placeholder="Digite e pressione Enter…",
                                    data=[],
                                    value=[],
                                    clearable=True,
                                ),
                                html.Div(id="settings-tags-feedback", style={"marginTop": 8}),
                            ],
                        ),
                    ]),

                    # ── TRL Docs ──────────────────────────────────────
                    dmc.TabsPanel(value="trl-docs", pt="md", children=[
                        dmc.Paper(
                            radius="md", p="md",
                            style={"background": "#25262b", "border": "1px solid #373A40"},
                            children=[
                                dmc.Text("Definições de cada nível TRL", fw=600, c="white", mb="md"),
                                html.Div(id="settings-trl-docs"),
                            ],
                        ),
                    ]),

                    # ── Preferences ───────────────────────────────────
                    dmc.TabsPanel(value="prefs", pt="md", children=[
                        dmc.Paper(
                            radius="md", p="md",
                            style={"background": "#25262b", "border": "1px solid #373A40"},
                            children=[
                                dmc.Stack(gap="sm", children=[
                                    dmc.Text("Preferências globais", fw=600, c="white"),
                                    dmc.Switch(
                                        id="settings-send-email",
                                        label="Enviar e-mail em atualizações de gate",
                                        checked=False,
                                        color="teal",
                                    ),
                                    dmc.Switch(
                                        id="settings-notify-deadlines",
                                        label="Notificar tarefas atrasadas automaticamente",
                                        checked=True,
                                        color="teal",
                                    ),
                                    dmc.NumberInput(
                                        id="settings-deadline-warning-days",
                                        label="Alertar X dias antes do prazo",
                                        value=7,
                                        min=1, max=60, step=1,
                                        w=200,
                                    ),
                                    dmc.Button(
                                        "Salvar preferências",
                                        id="settings-prefs-save-btn",
                                        color="teal",
                                        leftSection=icon("tabler:device-floppy", size=15),
                                        mt="sm",
                                    ),
                                    html.Div(id="settings-prefs-feedback"),
                                ]),
                            ],
                        ),
                    ]),
                ],
            ),
        ],
    )
