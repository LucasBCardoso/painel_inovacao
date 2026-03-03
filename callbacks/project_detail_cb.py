"""
Project Detail callbacks — OKRs, Gates, Tasks, Team, Meetings, Attachments, History
"""
from dash import Input, Output, State, ALL, MATCH, ctx, no_update, html
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from database import db, Project, TRLObjective, KeyResult, KRSubtask, GateReview, GateCheckItem, ProjectTask, TaskItem, Meeting, Attachment, ProjectHistory, User
from callbacks.helpers import (
    icon, trl_badge, priority_badge, progress_bar, gate_card,
    sector_badge, user_avatar, trl_color, STATUS_LABELS, STATUS_COLORS,
    GATE_STATUS_LABELS, GATE_STATUS_COLORS, build_gantt_figure,
)
from datetime import datetime, date


def _okr_row(okr: TRLObjective, is_admin: bool) -> dmc.AccordionItem:
    krs_content = []
    for kr in okr.key_results:
        subtasks = kr.subtasks
        done     = sum(1 for s in subtasks if s.completed)
        total    = len(subtasks)
        pct      = kr.completion_pct

        subtask_checks = [
            dmc.Checkbox(
                id={"type": "kr-subtask-check", "subtask_id": s.id},
                label=s.description,
                checked=s.completed,
                size="sm",
                disabled=not is_admin,
            ) for s in subtasks
        ]

        krs_content.append(
            dmc.Paper(p="sm", mb="xs", radius="md",
                      style={"borderLeft": f"3px solid {trl_color(okr.trl_from)}"},
                      children=dmc.Stack(gap="xs", children=[
                          dmc.Group(justify="space-between", children=[
                              dmc.Text(kr.description, size="sm", fw=500, style={"flex": 1}),
                              dmc.Text(f"{pct:.0f}%", size="sm", fw=700, c="teal"),
                          ]),
                          dmc.Group(gap=6, children=[
                              progress_bar(pct, size="xs"),
                              dmc.Text(f"{done}/{total}", size="xs", c="dimmed"),
                          ]),
                          dmc.Stack(gap=4, children=subtask_checks) if subtasks else
                          dmc.Text("Sem subtarefas", size="xs", c="dimmed"),
                      ]),
                      )
        )

    return dmc.AccordionItem(
        value=str(okr.id),
        children=[
            dmc.AccordionControl(
                dmc.Group(gap="sm", children=[
                    trl_badge(okr.trl_from, 20),
                    dmc.Text("→", c="dimmed", size="sm"),
                    trl_badge(okr.trl_to, 20),
                    dmc.Text(okr.objective, size="sm", fw=500),
                ]),
            ),
            dmc.AccordionPanel(
                dmc.Stack(gap="xs", children=[
                    dmc.Text(f"TRL {okr.trl_from} → TRL {okr.trl_to}", size="xs", c="dimmed"),
                    *krs_content,
                ])
            ),
        ],
    )


def _gate_panel(gate: GateReview, is_admin: bool) -> dmc.Paper:
    status  = gate.status
    color   = GATE_STATUS_COLORS.get(status, "gray")
    items   = gate.check_items

    style_map = {
        "pending":  {"border": "1px dashed #373A40"},
        "approved": {"border": "1px solid #2f9e44", "background": "rgba(47,158,68,.05)"},
        "rejected": {"border": "1px solid #fa5252", "background": "rgba(250,82,82,.05)"},
    }

    check_rows = [
        dmc.Group(justify="space-between", children=[
            dmc.Checkbox(
                id={"type": "gate-check", "item_id": item.id},
                label=item.text,
                checked=item.checked,
                size="sm",
                disabled=not is_admin,
            ),
        ]) for item in items
    ]

    status_select = dmc.Select(
        id={"type": "gate-status-select", "gate_id": gate.id},
        value=status,
        data=[
            {"value": "pending",  "label": "Pendente"},
            {"value": "approved", "label": "Aprovado"},
            {"value": "rejected", "label": "Reprovado"},
        ],
        size="xs",
        style={"width": 140},
        disabled=not is_admin,
    ) if is_admin else dmc.Badge(
        GATE_STATUS_LABELS.get(status, status), color=color, variant="light",
    )

    from database import GATE_DEFINITIONS
    defn = GATE_DEFINITIONS.get(gate.gate_id, {})

    return dmc.Paper(
        p="md", radius="md", mb="md",
        style=style_map.get(status, {}),
        children=dmc.Stack(gap="sm", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Group(gap="sm", children=[
                    icon("tabler:gate", 16, f"var(--mantine-color-{color}-5)"),
                    dmc.Text(defn.get("label", gate.gate_id), fw=700),
                    dmc.Text(defn.get("description", ""), size="xs", c="dimmed"),
                ]),
                status_select,
            ]),
            dmc.Divider(),
            *check_rows,
            # Reviewer + date
            dmc.Group(gap="md", children=[
                dmc.Text(f"Revisor: {gate.reviewer or '—'}", size="xs", c="dimmed"),
                dmc.Text(
                    f"Data: {gate.review_date.strftime('%d/%m/%Y') if gate.review_date else '—'}",
                    size="xs", c="dimmed",
                ),
            ]),
            # Notes
            dmc.Text(gate.notes or "", size="xs", c="dimmed") if gate.notes else html.Span(),
        ]),
    )


def register_projects_detail(app):

    # ── OKRs Panel ────────────────────────────────────────────────────────────
    @app.callback(
        Output("okrs-panel", "children"),
        Input("detail-tabs",    "value"),
        Input("detail-trigger", "data"),
        State("detail-project-id","data"),
        State("auth-store",       "data"),
    )
    def render_okrs(tab, _trigger, project_id, user):
        if tab != "okrs" or not project_id or not user:
            raise PreventUpdate
        p = Project.query.get(int(project_id))
        if not p:
            return dmc.Alert("Projeto não encontrado", color="red")
        is_admin = user.get("role") == "admin"

        if not p.okrs:
            return dmc.Center(py="xl", children=dmc.Text("Nenhum OKR cadastrado", c="dimmed"))

        return dmc.Stack(gap="md", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Text("Objetivos & Key Results por TRL", fw=600),
                dmc.Button("Adicionar OKR", size="xs", variant="light",
                           leftSection=icon("tabler:plus", 14),
                           id="okr-add-btn",
                           style={"display": "block" if is_admin else "none"}),
            ]),
            dmc.Accordion(
                multiple=True,
                children=[_okr_row(okr, is_admin) for okr in p.okrs],
            ),
        ])

    # ── Gates & Tasks Panel ───────────────────────────────────────────────────
    @app.callback(
        Output("gates-tasks-panel", "children"),
        Input("detail-tabs",     "value"),
        Input("detail-trigger",  "data"),
        State("detail-project-id","data"),
        State("auth-store",       "data"),
    )
    def render_gates(tab, _trigger, project_id, user):
        if tab != "gates" or not project_id or not user:
            raise PreventUpdate
        p = Project.query.get(int(project_id))
        if not p:
            return dmc.Alert("Projeto não encontrado", color="red")
        is_admin = user.get("role") == "admin"

        # Gates section
        gates_section = dmc.Stack(gap="sm", children=[
            dmc.Text("Gate Reviews", fw=600),
            *[_gate_panel(g, is_admin) for g in p.gate_reviews]
            or [dmc.Text("Nenhum gate configurado", c="dimmed", size="sm")],
        ])

        # Tasks accordion
        task_rows = []
        for t in p.tasks:
            status = t.computed_status
            color  = STATUS_COLORS.get(status, "gray")
            task_rows.append(
                dmc.AccordionItem(
                    value=str(t.id),
                    children=[
                        dmc.AccordionControl(
                            dmc.Group(gap="sm", children=[
                                dmc.Text(t.title, size="sm", fw=500),
                                dmc.Badge(STATUS_LABELS.get(status, status),
                                          color=color, variant="light", size="xs"),
                                priority_badge(t.priority),
                                dmc.Text(
                                    t.deadline.strftime("%d/%m/%Y") if t.deadline else "—",
                                    size="xs", c="dimmed" if not t.is_delayed else "red",
                                    ml="auto",
                                ),
                            ]),
                        ),
                        dmc.AccordionPanel(
                            dmc.Stack(gap="sm", children=[
                                dmc.Group(gap="md", children=[
                                    dmc.Stack(gap=0, children=[
                                        dmc.Text("Início estimado", size="xs", c="dimmed"),
                                        dmc.Text(
                                            t.estimated_start.strftime("%d/%m/%Y") if t.estimated_start else "—",
                                            size="sm",
                                        ),
                                    ]),
                                    dmc.Stack(gap=0, children=[
                                        dmc.Text("Fim estimado", size="xs", c="dimmed"),
                                        dmc.Text(
                                            t.estimated_end.strftime("%d/%m/%Y") if t.estimated_end else "—",
                                            size="sm",
                                        ),
                                    ]),
                                    dmc.Stack(gap=0, children=[
                                        dmc.Text("Responsáveis", size="xs", c="dimmed"),
                                        dmc.Group(gap=4, children=[
                                            user_avatar(u.to_dict(), 20) for u in t.assigned_users
                                        ] or [dmc.Text("—", size="sm")]),
                                    ]),
                                ]),
                                dmc.Text(t.description or "", size="sm", c="dimmed")
                                if t.description else html.Span(),
                                # Checklist
                                *[dmc.Checkbox(
                                    id={"type": "task-item-check", "item_id": item.id},
                                    label=item.description,
                                    checked=item.checked,
                                    size="sm",
                                    disabled=not is_admin,
                                ) for item in t.items],
                            ])
                        ),
                    ],
                )
            )

        tasks_section = dmc.Stack(gap="sm", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Text("Tarefas", fw=600),
                dmc.Button("Nova Tarefa", size="xs", variant="light",
                           leftSection=icon("tabler:plus", 14),
                           id="gate-task-add-btn",
                           style={"display": "block" if is_admin else "none"}),
            ]),
            dmc.Accordion(multiple=True, children=task_rows)
            if task_rows else dmc.Text("Nenhuma tarefa", c="dimmed", size="sm"),
        ])

        return dmc.SimpleGrid(
            cols={"base": 1, "md": 2}, spacing="md",
            children=[gates_section, tasks_section],
        )

    # ── Team Panel ────────────────────────────────────────────────────────────
    @app.callback(
        Output("team-panel", "children"),
        Input("detail-tabs",     "value"),
        Input("detail-trigger",  "data"),
        State("detail-project-id","data"),
        State("auth-store",       "data"),
    )
    def render_team(tab, _trigger, project_id, user):
        if tab != "team" or not project_id or not user:
            raise PreventUpdate
        p = Project.query.get(int(project_id))
        if not p:
            return dmc.Alert("Projeto não encontrado", color="red")

        if not p.responsible:
            return dmc.Center(py="xl", children=dmc.Text("Nenhum responsável", c="dimmed"))

        cards = []
        for u in p.responsible:
            tasks = [t for t in p.tasks if any(a.id == u.id for a in t.assigned_users)]
            done  = sum(1 for t in tasks if t.computed_status == "completed")
            cards.append(
                dmc.Paper(p="md", radius="md", children=dmc.Stack(gap="sm", children=[
                    dmc.Group(gap="sm", children=[
                        user_avatar(u.to_dict(), 40),
                        dmc.Stack(gap=0, children=[
                            dmc.Text(u.full_name, fw=600),
                            dmc.Text(u.position or "—", size="xs", c="dimmed"),
                        ]),
                    ]),
                    dmc.Divider(),
                    dmc.SimpleGrid(cols=2, spacing="xs", children=[
                        dmc.Stack(gap=0, align="center", children=[
                            dmc.Text(str(len(tasks)), fw=700, size="lg"),
                            dmc.Text("Tarefas", size="xs", c="dimmed"),
                        ]),
                        dmc.Stack(gap=0, align="center", children=[
                            dmc.Text(str(done), fw=700, size="lg", c="green"),
                            dmc.Text("Concluídas", size="xs", c="dimmed"),
                        ]),
                    ]),
                    progress_bar(round(done / len(tasks) * 100, 0) if tasks else 0.0),
                ]))
            )

        return dmc.SimpleGrid(
            cols={"base": 1, "sm": 2, "md": 3}, spacing="md", children=cards,
        )

    # ── Meetings Panel ────────────────────────────────────────────────────────
    @app.callback(
        Output("meetings-panel", "children"),
        Input("detail-tabs",      "value"),
        Input("detail-trigger",   "data"),
        State("detail-project-id","data"),
        State("auth-store",       "data"),
    )
    def render_meetings(tab, _trigger, project_id, user):
        if tab != "meetings" or not project_id or not user:
            raise PreventUpdate
        p = Project.query.get(int(project_id))
        if not p:
            return dmc.Alert("Projeto não encontrado", color="red")

        today = date.today()
        upcoming = [m for m in p.meetings if m.meeting_date >= today]
        past     = [m for m in p.meetings if m.meeting_date < today]

        def meeting_card(m: Meeting) -> dmc.Paper:
            is_past = m.meeting_date < today
            return dmc.Paper(p="sm", radius="md",
                             style={"opacity": 0.6 if is_past else 1},
                             children=dmc.Group(justify="space-between", children=[
                                 dmc.Group(gap="sm", children=[
                                     dmc.ThemeIcon(size="sm", variant="light",
                                                   color="gray" if is_past else "teal",
                                                   children=icon("tabler:calendar-event", 14)),
                                     dmc.Stack(gap=0, children=[
                                         dmc.Text(m.title, size="sm", fw=500),
                                         dmc.Text(
                                             f"{m.meeting_date.strftime('%d/%m/%Y')} "
                                             f"{m.meeting_time or ''}".strip(),
                                             size="xs", c="dimmed",
                                         ),
                                     ]),
                                 ]),
                                 dmc.Group(gap=4, children=[
                                     user_avatar(a.to_dict(), 20) for a in m.attendees[:4]
                                 ]),
                             ]))

        return dmc.Stack(gap="md", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Text("Reuniões", fw=600),
                dmc.Button("Nova Reunião", size="xs", variant="light",
                           leftSection=icon("tabler:plus", 14),
                           id="meeting-add-btn",
                           style={"display": "block" if user.get("role") == "admin" else "none"}),
            ]),
            dmc.Text("Próximas", size="xs", c="dimmed", tt="uppercase", style={"letterSpacing": ".06em"}),
            *[meeting_card(m) for m in upcoming] or
            [dmc.Text("Nenhuma reunião agendada", size="sm", c="dimmed")],
            dmc.Text("Anteriores", size="xs", c="dimmed", tt="uppercase",
                     style={"letterSpacing": ".06em"}) if past else html.Span(),
            *[meeting_card(m) for m in past[:5]],
        ])

    # ── Attachments Panel ─────────────────────────────────────────────────────
    @app.callback(
        Output("attachments-panel", "children"),
        Input("detail-tabs",        "value"),
        Input("detail-trigger",     "data"),
        State("detail-project-id",  "data"),
        State("auth-store",         "data"),
    )
    def render_attachments(tab, _trigger, project_id, user):
        if tab != "attachments" or not project_id or not user:
            raise PreventUpdate
        p = Project.query.get(int(project_id))
        if not p:
            return dmc.Alert("Projeto não encontrado", color="red")

        type_icons = {
            "document": "tabler:file-text",
            "image":    "tabler:photo",
            "video":    "tabler:video",
            "link":     "tabler:link",
            "folder":   "tabler:folder",
        }

        cards = [
            dmc.Paper(p="sm", radius="md", children=dmc.Group(gap="sm", children=[
                icon(type_icons.get(a.file_type, "tabler:file"), 20,
                     "var(--mantine-color-teal-5)"),
                dmc.Stack(gap=0, style={"flex": 1}, children=[
                    dmc.Anchor(a.name, href=a.url, target="_blank",
                               size="sm", fw=500),
                    dmc.Text(a.description or "", size="xs", c="dimmed"),
                ]),
                dmc.Text(a.added_at, size="xs", c="dimmed"),
            ])) for a in p.attachments
        ]

        return dmc.Stack(gap="sm", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Text("Anexos", fw=600),
                dmc.Button("Adicionar", size="xs", variant="light",
                           leftSection=icon("tabler:plus", 14),
                           id="attachment-add-btn",
                           style={"display": "block" if user.get("role") == "admin" else "none"}),
            ]),
            *cards or [dmc.Text("Nenhum anexo", c="dimmed", size="sm")],
        ])

    # ── History panel ─────────────────────────────────────────────────────────
    @app.callback(
        Output("history-panel",    "children"),
        Input("detail-tabs",       "value"),
        Input("detail-trigger",    "data"),
        State("detail-project-id", "data"),
        State("auth-store",        "data"),
    )
    def render_history(tab, _trigger, project_id, user):
        if tab != "history" or not project_id or not user:
            raise PreventUpdate
        p = Project.query.get(int(project_id))
        if not p:
            return dmc.Alert("Projeto não encontrado", color="red")

        type_icon_map = {
            "project_created":        ("tabler:plus", "teal"),
            "task_created":           ("tabler:list-check", "blue"),
            "task_completed":         ("tabler:check", "green"),
            "task_deadline_changed":  ("tabler:calendar-event", "orange"),
            "trl_advanced":           ("tabler:arrow-up", "violet"),
            "gate_approved":          ("tabler:gate", "green"),
            "gate_rejected":          ("tabler:gate", "red"),
        }

        items = []
        for h in p.history[:50]:
            ic_name, ic_color = type_icon_map.get(h.event_type, ("tabler:activity", "gray"))
            items.append(
                dmc.TimelineItem(
                    bullet=icon(ic_name, 14, f"var(--mantine-color-{ic_color}-5)"),
                    title=dmc.Text(h.event_type.replace("_", " ").title(), size="xs", c="dimmed"),
                    children=[
                        dmc.Text(h.description, size="sm"),
                        dmc.Text(
                            f"{h.user} · {h.timestamp}",
                            size="xs", c="dimmed",
                        ),
                    ],
                )
            )

        return dmc.Stack(gap="md", children=[
            dmc.Text("Histórico de Eventos", fw=600),
            dmc.Timeline(
                active=len(items) - 1,
                bulletSize=22,
                lineWidth=2,
                color="teal",
                children=items,
            ) if items else dmc.Text("Nenhum evento registrado", c="dimmed", size="sm"),
        ])

    # ── KR Subtask toggle ────────────────────────────────────────────────────
    @app.callback(
        Output("detail-trigger", "data", allow_duplicate=True),
        Input({"type": "kr-subtask-check", "subtask_id": ALL}, "checked"),
        State({"type": "kr-subtask-check", "subtask_id": ALL}, "id"),
        State("detail-project-id", "data"),
        State("detail-trigger",    "data"),
        State("auth-store",        "data"),
        prevent_initial_call=True,
    )
    def toggle_subtask(checked_list, id_list, project_id, trigger, user):
        if not user or user.get("role") != "admin":
            raise PreventUpdate
        triggered = ctx.triggered_id
        if not triggered or not isinstance(triggered, dict):
            raise PreventUpdate

        subtask_id  = triggered.get("subtask_id")
        # Find which index
        idx = next((i for i, d in enumerate(id_list) if d.get("subtask_id") == subtask_id), None)
        if idx is None:
            raise PreventUpdate

        from database import KRSubtask, now_brt
        st = KRSubtask.query.get(subtask_id)
        if not st:
            raise PreventUpdate

        st.completed    = checked_list[idx]
        st.completed_at = now_brt() if st.completed else None
        db.session.commit()

        # Recalc project progress
        if project_id:
            p = Project.query.get(int(project_id))
            if p:
                p.recalc_progress()
                db.session.commit()

        return (trigger or 0) + 1

    # ── Gate status change ───────────────────────────────────────────────────
    @app.callback(
        Output("detail-trigger", "data", allow_duplicate=True),
        Input({"type": "gate-status-select", "gate_id": ALL}, "value"),
        State({"type": "gate-status-select", "gate_id": ALL}, "id"),
        State("detail-project-id", "data"),
        State("detail-trigger",    "data"),
        State("auth-store",        "data"),
        prevent_initial_call=True,
    )
    def update_gate_status(values, ids, project_id, trigger, user):
        if not user or user.get("role") != "admin":
            raise PreventUpdate
        triggered = ctx.triggered_id
        if not triggered or not isinstance(triggered, dict):
            raise PreventUpdate

        gate_id = triggered.get("gate_id")
        idx = next((i for i, d in enumerate(ids) if d.get("gate_id") == gate_id), None)
        if idx is None:
            raise PreventUpdate

        gate = GateReview.query.get(gate_id)
        if not gate:
            raise PreventUpdate

        gate.status = values[idx]
        db.session.commit()

        p = Project.query.get(int(project_id))
        if p:
            db.session.add(ProjectHistory(
                project_id=p.id,
                event_type=f"gate_{values[idx]}",
                description=f"Gate {gate.gate_id} marcado como {values[idx]}",
                user_id=user.get("id"),
            ))
            db.session.commit()

        return (trigger or 0) + 1

    # ── Gate check item toggle ────────────────────────────────────────────────
    @app.callback(
        Output("detail-trigger", "data", allow_duplicate=True),
        Input({"type": "gate-check", "item_id": ALL}, "checked"),
        State({"type": "gate-check", "item_id": ALL}, "id"),
        State("detail-trigger", "data"),
        State("auth-store",     "data"),
        prevent_initial_call=True,
    )
    def toggle_gate_check(checked_list, id_list, trigger, user):
        if not user or user.get("role") != "admin":
            raise PreventUpdate
        triggered = ctx.triggered_id
        if not triggered or not isinstance(triggered, dict):
            raise PreventUpdate

        item_id = triggered.get("item_id")
        idx = next((i for i, d in enumerate(id_list) if d.get("item_id") == item_id), None)
        if idx is None:
            raise PreventUpdate

        item = GateCheckItem.query.get(item_id)
        if not item:
            raise PreventUpdate

        item.checked = checked_list[idx]
        db.session.commit()

        return (trigger or 0) + 1
