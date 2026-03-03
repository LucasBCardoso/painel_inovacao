"""
Project Detail — página com tabs completas
"""
import dash_mantine_components as dmc
from dash import html, dcc
from callbacks.helpers import icon
from database import db, Project, TRLObjective, KeyResult, KRSubtask, GateReview, ProjectTask
from callbacks.helpers import (
    trl_badge, priority_badge, progress_bar, gate_card,
    sector_badge, user_avatar, trl_color, trl_phase_color,
    STATUS_LABELS, STATUS_COLORS, build_gantt_figure, dark_fig, GATE_STATUS_LABELS,
    GATE_STATUS_COLORS, icon,
)


def layout(project_id: str, user: dict):
    try:
        pid = int(project_id)
    except (ValueError, TypeError):
        return dmc.Alert("Projeto inválido", color="red")

    p = Project.query.get(pid)
    if not p:
        return dmc.Alert("Projeto não encontrado", color="red")

    is_admin = user.get("role") == "admin"

    return dmc.Stack(gap="lg", children=[
        # Breadcrumb
        dmc.Breadcrumbs(children=[
            dmc.Anchor("Projetos", href="/projetos"),
            dmc.Text(p.name, c="dimmed"),
        ]),

        # Stores
        dcc.Store(id="detail-project-id", data=pid),
        dcc.Store(id="detail-trigger", data=0),

        # Header
        dmc.Paper(p="md", radius="md", children=[
            dmc.Group(justify="space-between", wrap="nowrap", children=[
                dmc.Group(gap="md", children=[
                    trl_badge(p.trl, 40),
                    dmc.Stack(gap=4, children=[
                        dmc.Group(gap="sm", children=[
                            dmc.Title(p.name, order=2, c="white"),
                            priority_badge(p.priority),
                            dmc.Badge("Atrasado", color="red", variant="filled", size="sm",
                                      style={"display": "block" if p.is_delayed else "none"}),
                        ]),
                        dmc.Group(gap="xs", children=[
                            dmc.Text(p.phase, size="xs", c="dimmed"),
                            dmc.Text("·", c="dimmed", size="xs"),
                            *[sector_badge(s) for s in p.sectors[:4]],
                            dmc.Text("·", c="dimmed", size="xs"),
                            dmc.Text(p.project_tag or "—", size="xs", c="dimmed"),
                        ]),
                    ]),
                ]),
                dmc.Stack(gap=4, align="flex-end", children=[
                    dmc.Text(f"{p.progress:.1f}%", size="xl", fw=900, c="teal"),
                    progress_bar(p.progress, size="sm"),
                    dmc.Text("Progresso Geral", size="xs", c="dimmed"),
                ]),
            ]),
        ]),

        # Tabs
        dmc.Tabs(
            id="detail-tabs",
            value="overview",
            children=[
                dmc.TabsList(children=[
                    dmc.TabsTab("Visão Geral",    leftSection=icon("tabler:info-circle", 14), value="overview"),
                    dmc.TabsTab("Gantt",          leftSection=icon("tabler:timeline", 14),    value="gantt"),
                    dmc.TabsTab("OKRs",           leftSection=icon("tabler:target", 14),      value="okrs"),
                    dmc.TabsTab("Gates & Tarefas",leftSection=icon("tabler:gate", 14),        value="gates"),
                    dmc.TabsTab("Equipe",         leftSection=icon("tabler:users", 14),       value="team"),
                    dmc.TabsTab("Reuniões",        leftSection=icon("tabler:calendar", 14),   value="meetings"),
                    dmc.TabsTab("Anexos",         leftSection=icon("tabler:paperclip", 14),   value="attachments"),
                    dmc.TabsTab("Histórico",      leftSection=icon("tabler:history", 14),     value="history"),
                ]),

                # ── Visão Geral ───────────────────────────────────────────────
                dmc.TabsPanel(value="overview", pt="md", children=[
                    dmc.SimpleGrid(cols={"base": 1, "md": 2}, spacing="md", children=[
                        dmc.Paper(p="md", radius="md", children=[
                            dmc.Text("Informações do Projeto", fw=600, mb="md"),
                            dmc.Stack(gap="sm", children=[
                                dmc.Group(justify="space-between", children=[
                                    dmc.Text("TRL Atual", size="sm", c="dimmed"),
                                    dmc.Group(gap="xs", children=[
                                        trl_badge(p.trl, 22),
                                        dmc.Text(f"TRL {p.trl}", fw=600),
                                    ]),
                                ]),
                                dmc.Group(justify="space-between", children=[
                                    dmc.Text("Fase", size="sm", c="dimmed"),
                                    dmc.Text(p.phase, fw=500),
                                ]),
                                dmc.Group(justify="space-between", children=[
                                    dmc.Text("Prioridade", size="sm", c="dimmed"),
                                    priority_badge(p.priority),
                                ]),
                                dmc.Group(justify="space-between", children=[
                                    dmc.Text("Data de Início", size="sm", c="dimmed"),
                                    dmc.Text(p.start_date.strftime("%d/%m/%Y") if p.start_date else "—", fw=500),
                                ]),
                                dmc.Group(justify="space-between", children=[
                                    dmc.Text("Meta de Entrega", size="sm", c="dimmed"),
                                    dmc.Text(p.target_date.strftime("%d/%m/%Y") if p.target_date else "—",
                                             fw=500, c="red" if p.is_delayed else None),
                                ]),
                                dmc.Group(justify="space-between", children=[
                                    dmc.Text("Tag", size="sm", c="dimmed"),
                                    dmc.Text(p.project_tag or "—", fw=500),
                                ]),
                                dmc.Divider(),
                                dmc.Text("Descrição", size="sm", c="dimmed"),
                                dmc.Text(p.description or "—", size="sm"),
                            ]),
                        ]),
                        dmc.Stack(gap="md", children=[
                            dmc.Paper(p="md", radius="md", children=[
                                dmc.Text("Gates de Avanço", fw=600, mb="md"),
                                dmc.Stack(gap="xs", children=[
                                    gate_card(g.to_dict()) for g in p.gate_reviews
                                ] or [dmc.Text("Nenhum gate configurado", size="sm", c="dimmed")]),
                            ]),
                        ]),
                    ]),
                ]),

                # ── Gantt ─────────────────────────────────────────────────────
                dmc.TabsPanel(value="gantt", pt="md", children=[
                    dmc.Paper(p="md", radius="md", children=[
                        dmc.Group(justify="space-between", mb="sm", children=[
                            dmc.Text("Gantt de Tarefas", fw=600),
                            dmc.Button(
                                "Adicionar Tarefa",
                                id="task-add-btn",
                                leftSection=icon("tabler:plus", 14),
                                size="xs", variant="light",
                                style={"display": "block" if is_admin else "none"},
                            ),
                        ]),
                        dcc.Graph(
                            id="project-gantt-chart",
                            config={"displayModeBar": False},
                            figure=build_gantt_figure([t.to_dict() for t in p.tasks]),
                            style={"height": max(300, len(p.tasks) * 44 + 100)},
                        ),
                    ]),
                    # Modal nova tarefa
                    dmc.Modal(
                        id="task-add-modal",
                        title=dmc.Text("Adicionar Tarefa", fw=700),
                        opened=False,
                        size="lg",
                        children=[
                            html.Div(id="task-add-form"),
                        ],
                    ),
                ]),

                # ── OKRs ─────────────────────────────────────────────────────
                dmc.TabsPanel(value="okrs", pt="md", children=[
                    html.Div(id="okrs-panel"),
                ]),

                # ── Gates & Tarefas ───────────────────────────────────────────
                dmc.TabsPanel(value="gates", pt="md", children=[
                    html.Div(id="gates-tasks-panel"),
                ]),

                # ── Equipe ────────────────────────────────────────────────────
                dmc.TabsPanel(value="team", pt="md", children=[
                    html.Div(id="team-panel"),
                ]),

                # ── Reuniões ─────────────────────────────────────────────────
                dmc.TabsPanel(value="meetings", pt="md", children=[
                    html.Div(id="meetings-panel"),
                ]),

                # ── Anexos ───────────────────────────────────────────────────
                dmc.TabsPanel(value="attachments", pt="md", children=[
                    html.Div(id="attachments-panel"),
                ]),

                # ── Histórico ────────────────────────────────────────────────
                dmc.TabsPanel(value="history", pt="md", children=[
                    html.Div(id="history-panel"),
                ]),
            ],
        ),

        # Modals globais do detalhe
        dmc.Modal(id="gate-edit-modal", title="Editar Gate Review",
                  size="lg", opened=False, children=[html.Div(id="gate-edit-form")]),
        dmc.Modal(id="kr-subtask-modal", title="Subtarefas do KR",
                  size="md", opened=False, children=[html.Div(id="kr-subtask-content")]),
    ])
