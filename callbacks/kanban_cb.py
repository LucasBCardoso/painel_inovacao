"""
Kanban TRL callbacks — Painel TRL Delta
"""
import json
from dash import Input, Output, State, ALL, ctx, no_update, html
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from database import db, Project, GateReview, project_sectors
from callbacks.helpers import (
    icon, trl_badge, priority_badge, progress_bar,
    gate_card, sector_badge, trl_color, trl_phase_color,
    STATUS_LABELS, user_avatar,
)
from sqlalchemy import select

PHASES = [
    {"label": "Descoberta",       "color": "violet", "trls": [1, 2, 3], "gate": "gate1"},
    {"label": "Desenvolvimento",  "color": "blue",   "trls": [4, 5, 6], "gate": "gate2"},
    {"label": "Industrialização", "color": "teal",   "trls": [7, 8, 9], "gate": None},
]


def _project_card(p: Project) -> dmc.Paper:
    """Card do projeto no kanban."""
    sectors = p.sectors[:2]
    return dmc.Paper(
        p="sm", mb="xs", radius="md",
        style={"cursor": "pointer", "borderLeft": f"3px solid {trl_color(p.trl)}"},
        id={"type": "kanban-card", "project_id": p.id},
        children=dmc.Stack(gap="xs", children=[
            # Nome + prioridade
            dmc.Group(justify="space-between", wrap="nowrap", children=[
                dmc.Text(p.name, size="xs", fw=600, lineClamp=2, style={"flex": 1}),
                priority_badge(p.priority),
            ]),
            # Progresso
            dmc.Group(gap=6, children=[
                progress_bar(p.progress, size="xs"),
                dmc.Text(f"{p.progress:.0f}%", size="xs", c="dimmed", style={"whiteSpace": "nowrap"}),
            ]),
            # Setores + responsáveis
            dmc.Group(justify="space-between", children=[
                dmc.Group(gap=4, children=[sector_badge(s) for s in sectors]),
                dmc.AvatarGroup(children=[
                    user_avatar(u.to_dict(), 20) for u in p.responsible[:3]
                ]),
            ]),
            # Atraso
            dmc.Badge("Atrasado", color="red", variant="light", size="xs",
                      style={"display": "block" if p.is_delayed else "none"}),
        ]),
    )


def _build_board(projects: list[Project], sector_filter=None, prio_filter=None) -> dmc.Group:
    if sector_filter:
        projects = [p for p in projects if any(s in (p.sectors or []) for s in sector_filter)]
    if prio_filter:
        projects = [p for p in projects if p.priority == prio_filter]

    phase_cols = []

    for phase in PHASES:
        trl_cols = []

        for trl in phase["trls"]:
            trl_projects = [p for p in projects if p.trl == trl]
            cards = [_project_card(p) for p in trl_projects] if trl_projects else [
                dmc.Text("—", size="xs", c="dimmed", ta="center", py="sm"),
            ]
            trl_cols.append(
                dmc.Paper(
                    p="sm", radius="md",
                    style={
                        "background": "#1f2023",
                        "border": f"1px solid {trl_color(trl)}33",
                        "minHeight": 140,
                        "minWidth": 160,
                        "maxWidth": 200,
                    },
                    children=dmc.Stack(gap="xs", children=[
                        dmc.Group(justify="space-between", children=[
                            trl_badge(trl, 22),
                            dmc.Text(f"TRL {trl}", size="xs", c="dimmed"),
                        ]),
                        dmc.Divider(mb="xs"),
                        *cards,
                    ]),
                )
            )

        # Gate column between phases (except last)
        if phase["gate"]:
            gate_col = dmc.Paper(
                p="sm", radius="md",
                style={
                    "background": "#18191c",
                    "border": "1px dashed #373A40",
                    "minHeight": 140,
                    "width": 100,
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "gap": "6px",
                },
                children=[
                    icon("tabler:gate", 20, "#5c5f66"),
                    dmc.Text("Gate", size="xs", c="dimmed"),
                    dmc.Badge(
                        phase["gate"].replace("gate", "Gate "),
                        color="gray", variant="outline", size="xs",
                    ),
                ],
            )
            trl_cols.append(gate_col)

        # Phase header + TRL columns
        phase_cols.append(
            dmc.Stack(gap="xs", children=[
                dmc.Group(gap="xs", children=[
                    icon(
                        {"Descoberta": "tabler:bulb",
                         "Desenvolvimento": "tabler:code",
                         "Industrialização": "tabler:factory"}[phase["label"]],
                        16, f"var(--mantine-color-{phase['color']}-5)"
                    ),
                    dmc.Text(phase["label"], fw=700, size="sm",
                             c=phase["color"]),
                    dmc.Badge(
                        str(sum(1 for p in projects if p.trl in phase["trls"])),
                        color=phase["color"], variant="light", size="xs", circle=True,
                    ),
                ]),
                dmc.Group(gap="xs", align="flex-start", wrap="nowrap",
                          children=trl_cols),
            ])
        )

    # Coluna Concluído (TRL 9 finalizado)
    done_projects = [p for p in projects if p.trl == 9 and p.progress >= 100]
    if True:  # sempre mostrar
        phase_cols.append(
            dmc.Stack(gap="xs", children=[
                dmc.Group(gap="xs", children=[
                    icon("tabler:check", 16, "var(--mantine-color-green-5)"),
                    dmc.Text("Concluído", fw=700, size="sm", c="green"),
                    dmc.Badge(str(len(done_projects)), color="green",
                              variant="light", size="xs", circle=True),
                ]),
                dmc.Paper(
                    p="sm", radius="md",
                    style={
                        "background": "#1a2620",
                        "border": "1px solid #2f9e4444",
                        "minHeight": 140,
                        "width": 180,
                    },
                    children=dmc.Stack(gap="xs", children=[
                        *([_project_card(p) for p in done_projects] or
                          [dmc.Text("Nenhum projeto concluído", size="xs",
                                    c="dimmed", ta="center", py="sm")]),
                    ]),
                ),
            ])
        )

    return html.Div(
        style={"overflowX": "auto", "paddingBottom": 12},
        children=[
            dmc.Group(gap="xl", align="flex-start", wrap="nowrap",
                      children=phase_cols),
        ],
    )


def register_kanban(app):

    # Render board
    @app.callback(
        Output("kanban-board", "children"),
        Input("url",                    "pathname"),
        Input("kanban-sector-filter",   "value"),
        Input("kanban-priority-filter", "value"),
        Input("project-trigger",        "data"),
        State("auth-store",             "data"),
    )
    def render_board(pathname, sectors, prio, _trigger, user):
        if pathname != "/kanban" or not user:
            raise PreventUpdate
        projects = Project.query.filter_by(is_active=True).all()
        return _build_board(projects, sectors, prio)

    # Open project modal on card click
    @app.callback(
        Output("kanban-project-modal", "opened"),
        Output("kanban-modal-title",   "children"),
        Output("kanban-modal-body",    "children"),
        Input({"type": "kanban-card", "project_id": ALL}, "n_clicks"),
        State("auth-store", "data"),
        prevent_initial_call=True,
    )
    def open_project_modal(n_clicks_list, user):
        if not any(n_clicks_list) or not user:
            raise PreventUpdate

        triggered = ctx.triggered_id
        if not triggered or not isinstance(triggered, dict):
            raise PreventUpdate

        project_id = triggered.get("project_id")
        p = Project.query.get(project_id)
        if not p:
            raise PreventUpdate

        title = dmc.Group(gap="sm", children=[
            trl_badge(p.trl, 28),
            dmc.Stack(gap=0, children=[
                dmc.Text(p.name, fw=700, size="md"),
                dmc.Text(p.phase, size="xs", c="dimmed"),
            ]),
            priority_badge(p.priority),
        ])

        gates = {g.gate_id: g.to_dict() for g in p.gate_reviews}

        body = dmc.Stack(gap="md", children=[
            # Descrição
            dmc.Paper(p="sm", radius="md", children=[
                dmc.Text("Descrição", size="xs", c="dimmed", mb=4),
                dmc.Text(p.description or "—", size="sm"),
            ]),
            # Datas + progresso
            dmc.SimpleGrid(cols=3, spacing="sm", children=[
                dmc.Paper(p="sm", radius="md", children=dmc.Stack(gap=2, children=[
                    dmc.Text("Início", size="xs", c="dimmed"),
                    dmc.Text(p.start_date.strftime("%d/%m/%Y") if p.start_date else "—", fw=600),
                ])),
                dmc.Paper(p="sm", radius="md", children=dmc.Stack(gap=2, children=[
                    dmc.Text("Meta", size="xs", c="dimmed"),
                    dmc.Text(p.target_date.strftime("%d/%m/%Y") if p.target_date else "—", fw=600,
                             c="red" if p.is_delayed else None),
                ])),
                dmc.Paper(p="sm", radius="md", children=dmc.Stack(gap=2, children=[
                    dmc.Text("Progresso", size="xs", c="dimmed"),
                    dmc.Text(f"{p.progress:.1f}%", fw=600, c="teal"),
                    progress_bar(p.progress),
                ])),
            ]),
            # Responsáveis
            dmc.Paper(p="sm", radius="md", children=[
                dmc.Text("Responsáveis", size="xs", c="dimmed", mb=6),
                dmc.Group(gap="sm", children=[
                    dmc.Group(gap=6, children=[
                        user_avatar(u.to_dict(), 28),
                        dmc.Text(u.full_name, size="sm"),
                    ]) for u in p.responsible
                ] or [dmc.Text("—", size="sm", c="dimmed")]),
            ]),
            # Gates
            dmc.Paper(p="sm", radius="md", children=[
                dmc.Text("Gate Reviews", size="xs", c="dimmed", mb=6),
                dmc.SimpleGrid(cols={"base": 1, "sm": 2}, spacing="xs", children=[
                    gate_card(g, compact=True) for g in (gates.values() if gates else [])
                ] or [dmc.Text("—", size="sm", c="dimmed")]),
            ]),
            # Botão ver projeto completo
            dmc.Anchor(
                dmc.Button(
                    "Ver Projeto Completo",
                    leftSection=icon("tabler:external-link", 16),
                    variant="light", fullWidth=True,
                ),
                href=f"/projetos/{p.id}",
            ),
        ])

        return True, title, body
