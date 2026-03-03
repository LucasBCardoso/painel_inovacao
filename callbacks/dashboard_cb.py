"""
Dashboard callbacks — Painel TRL Delta
"""
from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash import html
import plotly.graph_objects as go
import plotly.express as px
from database import db, Project, User, ProjectTask
from callbacks.helpers import dark_fig, trl_color, icon, priority_badge, progress_bar, user_avatar
from datetime import date


def _kpi_card(value, label, color="teal", icon_name="tabler:chart-bar"):
    return dmc.Paper(
        p="md", radius="md",
        style={"borderLeft": f"4px solid var(--delta-{color},#00afac)"},
        children=dmc.Group(justify="space-between", align="flex-start", children=[
            dmc.Stack(gap=2, children=[
                dmc.Text(str(value), size="xl", fw=900,
                         style={"color": f"var(--mantine-color-{color}-5)", "fontSize": 28}),
                dmc.Text(label, size="xs", c="dimmed",
                         style={"textTransform": "uppercase", "letterSpacing": ".05em"}),
            ]),
            dmc.ThemeIcon(size="lg", variant="light", color=color,
                          children=icon(icon_name, 22)),
        ]),
    )


def register_dashboard(app):

    @app.callback(
        Output("kpi-total-projects",    "children"),
        Output("kpi-in-progress",       "children"),
        Output("kpi-delayed",           "children"),
        Output("kpi-avg-progress",      "children"),
        Output("chart-by-trl",          "figure"),
        Output("chart-by-priority",     "figure"),
        Output("chart-by-sector",       "figure"),
        Output("chart-progress-status", "figure"),
        Output("chart-projects-gantt",  "figure"),
        Output("projects-summary-table","children"),
        Output("users-metrics-grid",    "children"),
        Input("url",                            "pathname"),
        Input("dashboard-refresh-btn",          "n_clicks"),
        State("auth-store",                     "data"),
    )
    def update_dashboard(pathname, _refresh, user):
        if pathname != "/" or not user:
            raise PreventUpdate

        projects = Project.query.filter_by(is_active=True).all()
        users    = User.query.filter_by(is_active=True).all()

        if not projects:
            empty = dmc.Text("Nenhum projeto cadastrado", c="dimmed", ta="center", py="xl")
            empty_fig = dark_fig(go.Figure())
            return (
                _kpi_card(0, "Total de Projetos"),
                _kpi_card(0, "Em Andamento", "blue"),
                _kpi_card(0, "Atrasados",    "red"),
                _kpi_card("0%","Progresso Médio"),
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                empty, empty,
            )

        today = date.today()

        # ── KPIs ─────────────────────────────────────────────────────────────
        total    = len(projects)
        delayed  = sum(1 for p in projects if p.is_delayed)
        avg_prog = round(sum(p.progress for p in projects) / total, 1)
        in_prog  = sum(1 for p in projects if 0 < p.progress < 100 and not p.is_delayed)

        kpi_total   = _kpi_card(total,   "Total de Projetos",       "teal",   "tabler:folder")
        kpi_prog    = _kpi_card(in_prog, "Em Andamento",            "blue",   "tabler:activity")
        kpi_delayed = _kpi_card(delayed, "Atrasados",               "red",    "tabler:alert-triangle")
        kpi_avg     = _kpi_card(f"{avg_prog}%","Progresso Médio",   "green",  "tabler:chart-line")

        # ── Chart: por TRL ────────────────────────────────────────────────────
        trl_count = {}
        for p in projects:
            trl_count[p.trl] = trl_count.get(p.trl, 0) + 1
        trls   = sorted(trl_count.keys())
        counts = [trl_count[t] for t in trls]
        colors = [trl_color(t) for t in trls]
        fig_trl = go.Figure(go.Bar(
            x=[f"TRL {t}" for t in trls],
            y=counts,
            marker_color=colors,
            text=counts,
            textposition="outside",
        ))
        fig_trl.update_layout(title=None, showlegend=False, height=260, yaxis_title="Quantidade")
        dark_fig(fig_trl)

        # ── Chart: por prioridade ─────────────────────────────────────────────
        prio_map   = {"alta": 0, "media": 0, "baixa": 0}
        prio_color = {"alta": "#fa5252", "media": "#fd7e14", "baixa": "#228be6"}
        for p in projects:
            prio_map[p.priority] = prio_map.get(p.priority, 0) + 1
        fig_prio = go.Figure(go.Pie(
            labels=["Alta", "Média", "Baixa"],
            values=[prio_map["alta"], prio_map["media"], prio_map["baixa"]],
            hole=.55,
            marker_colors=[prio_color["alta"], prio_color["media"], prio_color["baixa"]],
        ))
        fig_prio.update_traces(textposition="inside", textinfo="percent+label")
        fig_prio.update_layout(height=260, showlegend=True)
        dark_fig(fig_prio)

        # ── Chart: por setor ──────────────────────────────────────────────────
        sector_count = {}
        for p in projects:
            for s in p.sectors:
                sector_count[s] = sector_count.get(s, 0) + 1
        if sector_count:
            sec_names = list(sector_count.keys())
            sec_vals  = [sector_count[s] for s in sec_names]
            fig_sector = go.Figure(go.Bar(
                y=sec_names, x=sec_vals, orientation="h",
                marker_color="#00afac",
                text=sec_vals, textposition="auto",
            ))
            fig_sector.update_layout(height=260, xaxis_title="Projetos")
            dark_fig(fig_sector)
        else:
            fig_sector = dark_fig(go.Figure())

        # ── Chart: status de progresso (radar / bar) ───────────────────────
        ranges = [(0, 25, "0–25%"), (25, 50, "25–50%"), (50, 75, "50–75%"), (75, 100, "75–100%")]
        range_counts = [sum(1 for p in projects if lo <= p.progress < hi) for lo, hi, _ in ranges]
        range_labels = [r[2] for r in ranges]
        fig_status = go.Figure(go.Bar(
            x=range_labels, y=range_counts,
            marker_color=["#fa5252", "#fd7e14", "#228be6", "#2f9e44"],
            text=range_counts, textposition="outside",
        ))
        fig_status.update_layout(height=260, yaxis_title="Projetos", showlegend=False)
        dark_fig(fig_status)

        # ── Gantt macro por projetos ───────────────────────────────────────
        import pandas as pd
        gantt_tasks = []
        for p in sorted(projects, key=lambda x: x.trl):
            if p.start_date and p.target_date:
                gantt_tasks.append({
                    "name":       p.name,
                    "trl":        p.trl,
                    "start":      p.start_date,
                    "end":        p.target_date,
                    "progress":   p.progress,
                    "is_delayed": p.is_delayed,
                })

        fig_gantt = go.Figure()
        for gt in gantt_tasks:
            color = "#fa5252" if gt["is_delayed"] else trl_color(gt["trl"])
            duration = (pd.to_datetime(gt["end"]) - pd.to_datetime(gt["start"])).days
            fig_gantt.add_trace(go.Bar(
                name=gt["name"],
                x=[duration],
                y=[f"TRL {gt['trl']} · {gt['name'][:25]}"],
                base=[pd.to_datetime(gt["start"])],
                orientation="h",
                marker_color=color,
                marker_line_width=0,
                text=f"{gt['progress']:.0f}%",
                textposition="inside",
                hovertemplate=(
                    f"<b>{gt['name']}</b><br>"
                    f"TRL: {gt['trl']}<br>"
                    f"Início: {gt['start']}<br>"
                    f"Meta: {gt['end']}<br>"
                    f"Progresso: {gt['progress']:.1f}%<extra></extra>"
                ),
                showlegend=False,
                width=0.7,
            ))

        if gantt_tasks:
            fig_gantt.add_vline(
                x=pd.to_datetime(today).value / 1e6,
                line_dash="dot", line_color="#00afac", line_width=2,
                annotation_text="Hoje", annotation_font_color="#00afac", annotation_font_size=11,
            )
        fig_gantt.update_layout(
            barmode="overlay",
            height=max(250, len(gantt_tasks) * 40 + 80),
            xaxis=dict(type="date"),
            yaxis=dict(autorange="reversed"),
        )
        dark_fig(fig_gantt)

        # ── Projects summary table ────────────────────────────────────────
        table_rows = []
        for p in sorted(projects, key=lambda x: -x.progress):
            from callbacks.helpers import trl_badge, priority_badge, progress_bar, sector_badge
            responsibles = ", ".join(u.full_name for u in p.responsible[:2])
            if len(p.responsible) > 2:
                responsibles += f" +{len(p.responsible)-2}"

            table_rows.append(
                html.Tr([
                    html.Td(dmc.Group(gap="xs", children=[
                        trl_badge(p.trl, 24),
                        dmc.Text(p.name, size="sm", fw=500),
                    ])),
                    html.Td(dmc.Group(gap=4, children=[sector_badge(s) for s in p.sectors[:2]])),
                    html.Td(priority_badge(p.priority)),
                    html.Td(dmc.Group(gap=6, children=[
                        progress_bar(p.progress, size="xs"),
                        dmc.Text(f"{p.progress:.0f}%", size="xs", c="dimmed"),
                    ], style={"minWidth": 100})),
                    html.Td(dmc.Text(responsibles, size="xs", c="dimmed")),
                    html.Td(dmc.Badge("Atrasado" if p.is_delayed else "OK",
                                      color="red" if p.is_delayed else "green",
                                      variant="light", size="xs")),
                ])
            )

        summary_table = dmc.Paper(
            p="md", radius="md",
            children=[
                dmc.Text("Resumo de Projetos", fw=600, mb="sm"),
                dmc.Table(
                    striped=True, highlightOnHover=True, withTableBorder=True,
                    withColumnBorders=True,
                    children=[
                        html.Thead(html.Tr([
                            html.Th("Projeto"), html.Th("Setores"), html.Th("Prioridade"),
                            html.Th("Progresso"), html.Th("Responsáveis"), html.Th("Status"),
                        ])),
                        html.Tbody(table_rows),
                    ],
                ),
            ],
        )

        # ── Users metrics grid ────────────────────────────────────────────
        user_cards = []
        for u in users:
            tasks_resp = ProjectTask.query.filter(
                ProjectTask.assigned_users.any(id=u.id),
                ProjectTask.project_id.in_([p.id for p in projects]),
            ).all()
            total_t    = len(tasks_resp)
            done_t     = sum(1 for t in tasks_resp if t.computed_status == "completed")
            delayed_t  = sum(1 for t in tasks_resp if t.computed_status == "delayed")

            user_cards.append(
                dmc.Paper(
                    p="md", radius="md",
                    children=dmc.Stack(gap="sm", children=[
                        dmc.Group(gap="sm", children=[
                            user_avatar(u.to_dict(), 36),
                            dmc.Stack(gap=0, children=[
                                dmc.Text(u.full_name, fw=600, size="sm"),
                                dmc.Text(u.position or "—", size="xs", c="dimmed"),
                            ]),
                            dmc.Badge("Admin" if u.role == "admin" else "User",
                                      color="teal" if u.role == "admin" else "gray",
                                      variant="light", size="xs", ml="auto"),
                        ]),
                        dmc.Divider(),
                        dmc.SimpleGrid(cols=3, spacing="xs", children=[
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(str(total_t), fw=700, size="lg"),
                                dmc.Text("Tarefas", size="xs", c="dimmed"),
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(str(done_t), fw=700, size="lg", c="green"),
                                dmc.Text("Conc.", size="xs", c="dimmed"),
                            ]),
                            dmc.Stack(gap=0, align="center", children=[
                                dmc.Text(str(delayed_t), fw=700, size="lg",
                                         c="red" if delayed_t else "dimmed"),
                                dmc.Text("Atras.", size="xs", c="dimmed"),
                            ]),
                        ]),
                        progress_bar(
                            round(done_t / total_t * 100, 0) if total_t else 0.0
                        ),
                    ]),
                )
            )

        users_grid = dmc.SimpleGrid(
            cols={"base": 1, "sm": 2, "md": 3},
            spacing="md",
            children=user_cards or [dmc.Text("Nenhum usuário", c="dimmed", ta="center")],
        )

        return (
            kpi_total, kpi_prog, kpi_delayed, kpi_avg,
            fig_trl, fig_prio, fig_sector, fig_status, fig_gantt,
            summary_table, users_grid,
        )
