"""
Projects callbacks — Painel TRL Delta
"""
from dash import Input, Output, State, no_update, html, ctx
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from database import db, Project
from callbacks.helpers import (
    icon, trl_badge, priority_badge, progress_bar,
    sector_badge, trl_color, user_avatar,
)
from datetime import date


def _project_list_card(p: Project) -> dmc.Paper:
    return dmc.Paper(
        p="md", radius="md",
        style={"cursor": "pointer", "borderLeft": f"4px solid {trl_color(p.trl)}"},
        # Link direto ao projeto
        children=dmc.Anchor(
            href=f"/projetos/{p.id}",
            underline="never",
            children=dmc.Stack(gap="sm", children=[
                dmc.Group(justify="space-between", wrap="nowrap", children=[
                    dmc.Group(gap="sm", children=[
                        trl_badge(p.trl, 28),
                        dmc.Stack(gap=0, style={"flex": 1}, children=[
                            dmc.Text(p.name, fw=600, size="sm", c="white"),
                            dmc.Text(p.project_tag or "—", size="xs", c="dimmed"),
                        ]),
                    ]),
                    dmc.Group(gap="xs", children=[
                        priority_badge(p.priority),
                        dmc.Badge("Atrasado", color="red", variant="filled", size="xs",
                                  style={"display": "block" if p.is_delayed else "none"}),
                    ]),
                ]),
                dmc.Text(
                    (p.description or "")[:100] + ("…" if p.description and len(p.description) > 100 else ""),
                    size="xs", c="dimmed",
                ),
                dmc.Group(justify="space-between", children=[
                    dmc.Group(gap=4, children=[sector_badge(s) for s in p.sectors[:3]]),
                    dmc.Group(gap=6, children=[
                        progress_bar(p.progress, size="xs"),
                        dmc.Text(f"{p.progress:.0f}%", size="xs", c="dimmed"),
                    ], style={"minWidth": 120}),
                ]),
                dmc.Group(justify="space-between", children=[
                    dmc.Group(gap=4, children=[
                        user_avatar(u.to_dict(), 22) for u in p.responsible[:4]
                    ]),
                    dmc.Group(gap="xs", children=[
                        icon("tabler:calendar", 12, "#5c5f66"),
                        dmc.Text(
                            p.target_date.strftime("%d/%m/%Y") if p.target_date else "—",
                            size="xs", c="dimmed",
                        ),
                    ]),
                ]),
            ]),
        ),
    )


def register_projects(app):

    @app.callback(
        Output("projects-list", "children"),
        Input("url",                       "pathname"),
        Input("projects-search",           "value"),
        Input("projects-sector-filter",    "value"),
        Input("projects-priority-filter",  "value"),
        Input("projects-trl-filter",       "value"),
        Input("project-trigger",           "data"),
        State("auth-store",                "data"),
    )
    def render_projects(pathname, search, sectors, priority, trl_filter, _t, user):
        if pathname != "/projetos" or not user:
            raise PreventUpdate

        query = Project.query.filter_by(is_active=True)

        if trl_filter:
            query = query.filter(Project.trl == int(trl_filter))
        if priority:
            query = query.filter(Project.priority == priority)

        projects = query.order_by(Project.trl, Project.name).all()

        # Filter by sector (Python side because it's a many-to-many via association table)
        if sectors:
            projects = [p for p in projects if any(s in (p.sectors or []) for s in sectors)]

        # Filter by search
        if search:
            search_lower = search.strip().lower()
            projects = [p for p in projects
                        if search_lower in p.name.lower()
                        or (p.description and search_lower in p.description.lower())
                        or (p.project_tag and search_lower in p.project_tag.lower())]

        if not projects:
            return dmc.Center(
                py="xl",
                children=dmc.Stack(align="center", gap="sm", children=[
                    icon("tabler:folder-x", 40, "#5c5f66"),
                    dmc.Text("Nenhum projeto encontrado", size="lg", c="dimmed"),
                    dmc.Text("Ajuste os filtros ou crie um novo projeto", size="sm", c="dimmed"),
                ]),
            )

        # Group by TRL
        trl_groups: dict[int, list[Project]] = {}
        for p in projects:
            trl_groups.setdefault(p.trl, []).append(p)

        sections = []
        for trl in sorted(trl_groups.keys()):
            trl_projects = trl_groups[trl]
            phase = trl_projects[0].phase

            sections.append(dmc.Stack(gap="sm", children=[
                dmc.Group(gap="sm", children=[
                    trl_badge(trl, 26),
                    dmc.Text(f"TRL {trl}", fw=700, size="sm"),
                    dmc.Text(f"· {phase}", size="sm", c="dimmed"),
                    dmc.Badge(str(len(trl_projects)), color="gray", variant="light",
                              size="xs", circle=True),
                ]),
                dmc.SimpleGrid(
                    cols={"base": 1, "sm": 2, "lg": 3},
                    spacing="sm",
                    children=[_project_list_card(p) for p in trl_projects],
                ),
            ]))

        return dmc.Stack(gap="xl", children=sections)
