"""
Report callbacks — Painel TRL Delta
"""
from datetime import date
from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import plotly.graph_objects as go
from database import db, Project, TRLObjective, KeyResult, GateReview, ProjectTask, ProjectHistory, User
from callbacks.helpers import (
    icon, dark_fig, trl_badge, status_badge, priority_badge,
    progress_bar, build_gantt_figure, gate_card, GATE_STATUS_LABELS
)


def register_report(app):

    # Populate project dropdown
    @app.callback(
        Output("report-project-select", "data"),
        Input("url", "pathname"),
        State("auth-store", "data"),
    )
    def populate_report_projects(pathname, user):
        if pathname != "/relatorio" or not user:
            raise PreventUpdate
        projects = Project.query.filter_by(is_active=True).order_by(Project.name).all()
        return [{"value": str(p.id), "label": p.name} for p in projects]

    # Generate report
    @app.callback(
        Output("report-content", "children"),
        Input("report-gen-btn", "n_clicks"),
        State("report-project-select", "value"),
        State("report-date-from", "value"),
        State("report-date-to",   "value"),
        State("auth-store",       "data"),
        prevent_initial_call=True,
    )
    def generate_report(n, proj_id, date_from, date_to, user):
        if not n or not proj_id or not user:
            return dmc.Alert(
                "Selecione um projeto e clique em Gerar.",
                color="blue", variant="light",
            )

        p = Project.query.get(int(proj_id))
        if not p:
            raise PreventUpdate

        today = date.today()

        # ── Summary header ────────────────────────────────────────────────
        header = dmc.Paper(
            radius="md", p="xl", mb="md",
            style={"background": "#25262b", "border": "1px solid #373A40"},
            children=[
                dmc.Group(
                    justify="space-between",
                    children=[
                        dmc.Stack(gap=2, children=[
                            dmc.Group(gap="xs", children=[
                                trl_badge(p.trl_level, size="lg"),
                                dmc.Title(p.name, order=2, c="white"),
                            ]),
                            dmc.Text(p.description or "", c="dimmed", size="sm"),
                            dmc.Group(gap="xs", mt=4, children=[
                                dmc.Badge(p.priority.upper(), color={"alta":"red","media":"orange","baixa":"blue"}.get(p.priority,"gray"), variant="light"),
                                dmc.Badge(p.sector or "-", color="cyan", variant="outline"),
                                dmc.Badge(p.status.replace("_"," ").title(), color="teal", variant="filled"),
                            ]),
                        ]),
                        dmc.RingProgress(
                            size=100,
                            sections=[{"value": p.progress, "color": "teal"}],
                            label=dmc.Text(f"{p.progress}%", ta="center", fw=700, c="teal"),
                        ),
                    ],
                ),
            ],
        )

        # ── OKRs / KRs ───────────────────────────────────────────────────
        okr_rows = []
        for obj in p.objectives:
            kr_rows = []
            for kr in obj.key_results:
                pct = kr.completion_pct
                kr_rows.append(
                    dmc.TableTr(children=[
                        dmc.TableTd(kr.title),
                        dmc.TableTd(f"{kr.achieved_value} / {kr.target_value} {kr.unit or ''}"),
                        dmc.TableTd(
                            dmc.Progress(value=pct, color="teal" if pct >= 70 else "orange" if pct >= 40 else "red", size="sm"),
                        ),
                        dmc.TableTd(dmc.Text(f"{pct:.0f}%", size="sm", fw=600)),
                    ])
                )
            okr_rows.append(
                dmc.Stack(gap="xs", mb="sm", children=[
                    dmc.Text(f"Objetivo: {obj.title}", fw=600, c="white"),
                    dmc.Table(
                        withTableBorder=True, withColumnBorders=True,
                        striped=True, highlightOnHover=True,
                        children=[
                            dmc.TableThead(dmc.TableTr([
                                dmc.TableTh("Key Result"), dmc.TableTh("Valor"), dmc.TableTh("Progresso"), dmc.TableTh("%"),
                            ])),
                            dmc.TableTbody(kr_rows),
                        ],
                    ),
                ])
            )

        okr_section = dmc.Paper(
            radius="md", p="md", mb="md",
            style={"background": "#1A1B1E", "border": "1px solid #373A40"},
            children=[
                dmc.Group(gap="xs", mb="sm", children=[
                    icon("tabler:target", size=18, color="#00afac"),
                    dmc.Title("OKRs / Key Results", order=4, c="white"),
                ]),
                dmc.Stack(gap="xs", children=okr_rows) if okr_rows else dmc.Text("Nenhum OKR cadastrado.", c="dimmed", size="sm"),
            ],
        )

        # ── Gates ─────────────────────────────────────────────────────────
        gates_items = []
        for g in p.gate_reviews:
            status_color = {"pending":"yellow","approved":"green","rejected":"red"}.get(g.status,"gray")
            gates_items.append(
                dmc.Group(gap="xs", mb=4, children=[
                    icon(f"tabler:{'check-circle' if g.status == 'approved' else 'clock' if g.status == 'pending' else 'x-circle'}", size=16, color=status_color),
                    dmc.Text(f"Gate {g.gate_number}: {GATE_STATUS_LABELS.get(g.status,g.status)}", size="sm", c="white"),
                    dmc.Text(f"(Revisão {g.review_date.strftime('%d/%m/%Y') if g.review_date else '—'})", size="xs", c="dimmed"),
                ])
            )

        gates_section = dmc.Paper(
            radius="md", p="md", mb="md",
            style={"background": "#1A1B1E", "border": "1px solid #373A40"},
            children=[
                dmc.Group(gap="xs", mb="sm", children=[
                    icon("tabler:shield-check", size=18, color="#00afac"),
                    dmc.Title("Gate Reviews", order=4, c="white"),
                ]),
                dmc.Stack(gap=2, children=gates_items) if gates_items else dmc.Text("Sem gates.", c="dimmed", size="sm"),
            ],
        )

        # ── Tasks Gantt ───────────────────────────────────────────────────
        tasks = p.tasks
        gantt_fig = build_gantt_figure(
            [{"title": t.title, "start_date": t.start_date, "deadline": t.deadline,
              "status": t.computed_status, "responsible": None} for t in tasks],
            today,
        )
        gantt_section = dmc.Paper(
            radius="md", p="md", mb="md",
            style={"background": "#1A1B1E", "border": "1px solid #373A40"},
            children=[
                dmc.Group(gap="xs", mb="sm", children=[
                    icon("tabler:chart-gantt", size=18, color="#00afac"),
                    dmc.Title("Tarefas / Cronograma", order=4, c="white"),
                ]),
                dmc.LineChart(
                    h=max(200, len(tasks) * 35),
                    data=[],
                ) if not tasks else
                dmc.AreaChart(h=20, data=[]) if False else  # placeholder branch
                html.Div(style={"height": max(200, len(tasks) * 40)},
                         children=[__import__("dash").dcc.Graph(figure=gantt_fig, config={"displayModeBar": False})]),
            ],
        )

        # ── History ───────────────────────────────────────────────────────
        hist_q = p.history.order_by(ProjectHistory.created_at.desc())  # type: ignore
        if date_from:
            from datetime import datetime
            hist_q = hist_q.filter(ProjectHistory.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            from datetime import datetime
            hist_q = hist_q.filter(ProjectHistory.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))
        hist_items = hist_q.limit(30).all()

        history_items = []
        for h in hist_items:
            history_items.append(
                dmc.TimelineItem(
                    title=h.action,
                    children=[
                        dmc.Text(h.details or "", size="xs", c="dimmed"),
                        dmc.Text(h.created_at.strftime("%d/%m/%Y %H:%M"), size="xs", c="dimmed"),
                    ],
                )
            )

        history_section = dmc.Paper(
            radius="md", p="md", mb="md",
            style={"background": "#1A1B1E", "border": "1px solid #373A40"},
            children=[
                dmc.Group(gap="xs", mb="sm", children=[
                    icon("tabler:history", size=18, color="#00afac"),
                    dmc.Title("Histórico de Atividades", order=4, c="white"),
                ]),
                dmc.Timeline(
                    active=len(history_items) - 1,
                    color="teal",
                    bulletSize=12,
                    lineWidth=1,
                    children=history_items,
                ) if history_items else dmc.Text("Sem histórico.", c="dimmed", size="sm"),
            ],
        )

        return dmc.Stack(gap="md", children=[header, okr_section, gates_section, gantt_section, history_section])
