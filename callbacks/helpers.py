"""
Helpers compartilhados — Painel TRL Delta
"""
import plotly.graph_objects as go
from dash_iconify import DashIconify
import dash_mantine_components as dmc
from database import PRIORITY_COLORS, TRL_COLORS, GATE_DEFINITIONS

# ── Icon helper ───────────────────────────────────────────────────────────────
def icon(name, size=18, color=None):
    return DashIconify(icon=name, width=size, color=color)


# ── Color maps ────────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "pending":     "gray",
    "in_progress": "blue",
    "completed":   "green",
    "delayed":     "red",
}
STATUS_LABELS = {
    "pending":     "Pendente",
    "in_progress": "Em Andamento",
    "completed":   "Concluída",
    "delayed":     "Atrasada",
}
PRIORITY_LABELS = {
    "alta":  "Alta",
    "media": "Média",
    "baixa": "Baixa",
}
GATE_STATUS_COLORS = {
    "pending":  "gray",
    "approved": "green",
    "rejected": "red",
}
GATE_STATUS_LABELS = {
    "pending":  "Pendente",
    "approved": "Aprovado",
    "rejected": "Reprovado",
}


def trl_color(trl: int) -> str:
    return TRL_COLORS.get(trl, "#228be6")


def trl_phase_color(trl: int) -> str:
    if trl <= 3: return "violet"
    if trl <= 6: return "blue"
    if trl <= 8: return "teal"
    return "green"


# ── Plotly dark theme ─────────────────────────────────────────────────────────
def dark_fig(fig: go.Figure) -> go.Figure:
    """Aplica o tema dark Delta ao figure Plotly."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#C1C2C5", size=12),
        margin=dict(l=10, r=10, t=34, b=10),
        legend=dict(
            bgcolor="rgba(37,38,43,.8)",
            bordercolor="#373A40",
            borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            gridcolor="#373A40",
            linecolor="#373A40",
            tickcolor="#5c5f66",
            zerolinecolor="#373A40",
        ),
        yaxis=dict(
            gridcolor="#373A40",
            linecolor="#373A40",
            tickcolor="#5c5f66",
            zerolinecolor="#373A40",
        ),
        colorway=["#00afac", "#228be6", "#7950f2", "#2f9e44", "#fd7e14", "#fa5252"],
    )
    return fig


# ── TRL badge component ───────────────────────────────────────────────────────
def trl_badge(trl: int, size: int = 28) -> dmc.Avatar:
    color = trl_color(trl)
    return dmc.Avatar(
        str(trl),
        size=size,
        radius="xl",
        style={"background": color, "color": "#fff", "fontWeight": 800, "fontSize": 12},
    )


# ── Priority badge ────────────────────────────────────────────────────────────
def priority_badge(priority: str) -> dmc.Badge:
    color = {"alta": "red", "media": "orange", "baixa": "blue"}.get(priority, "gray")
    return dmc.Badge(PRIORITY_LABELS.get(priority, priority), color=color, variant="light", size="sm")


# ── Status badge ──────────────────────────────────────────────────────────────
def status_badge(status: str) -> dmc.Badge:
    color = STATUS_COLORS.get(status, "gray")
    return dmc.Badge(STATUS_LABELS.get(status, status), color=color, variant="light", size="sm")


# ── Progress bar helper ───────────────────────────────────────────────────────
def progress_bar(value: float, color: str = "teal", size: str = "sm") -> dmc.Progress:
    return dmc.Progress(value=value, color=color, size=size, radius="xl")


# ── Avatar initials ───────────────────────────────────────────────────────────
def user_avatar(user_dict: dict, size: int = 28) -> dmc.Avatar:
    name = user_dict.get("full_name", "?")
    initials = "".join(w[0].upper() for w in name.split()[:2])
    color_map = {
        "teal": "#00afac", "blue": "#228be6", "violet": "#7950f2",
        "cyan": "#0bc5ea", "green": "#2f9e44", "orange": "#fd7e14",
        "red":  "#fa5252", "grape": "#ae3ec9",
    }
    bg = color_map.get(user_dict.get("avatar_color", "teal"), "#00afac")
    return dmc.Avatar(
        initials,
        size=size,
        radius="xl",
        style={"background": bg, "color": "#fff", "fontWeight": 700, "fontSize": max(10, size // 2 - 2)},
    )


# ── Gantt bar builder (Plotly) ────────────────────────────────────────────────
def build_gantt_figure(tasks: list, today=None) -> go.Figure:
    """Cria Gantt horizontal com barras estimadas (cinza) e reais (coloridas)."""
    from datetime import date as dt_date
    import pandas as pd

    if today is None:
        today = dt_date.today()

    if not tasks:
        fig = go.Figure()
        dark_fig(fig)
        fig.update_layout(title="Nenhuma tarefa disponível", height=160)
        return fig

    fig = go.Figure()
    y_labels = []

    for i, t in enumerate(tasks):
        label = t.get("title", f"Tarefa {i+1}")
        y_labels.append(label)

        # Barra estimada (fundo cinza)
        est_start = t.get("estimated_start") or t.get("start_date")
        est_end   = t.get("estimated_end")   or t.get("deadline")
        if est_start and est_end:
            fig.add_trace(go.Bar(
                name="Estimado" if i == 0 else None,
                showlegend=i == 0,
                x=[(pd.to_datetime(est_end) - pd.to_datetime(est_start)).days],
                y=[label],
                base=[pd.to_datetime(est_start)],
                orientation="h",
                marker_color="rgba(92,95,102,.35)",
                marker_line_width=0,
                width=0.4,
            ))

        # Barra real (colorida por priority)
        real_start = t.get("actual_start") or t.get("start_date")
        real_end   = t.get("actual_end")   or t.get("deadline")
        status     = t.get("status", "pending")
        color_map  = {
            "completed":   "#2f9e44",
            "in_progress": "#228be6",
            "delayed":     "#fa5252",
            "pending":     "#5c5f66",
        }
        bar_color = color_map.get(status, "#00afac")

        if real_start and real_end:
            fig.add_trace(go.Bar(
                name=STATUS_LABELS.get(status, status) if i == 0 else None,
                showlegend=i == 0,
                x=[(pd.to_datetime(real_end) - pd.to_datetime(real_start)).days],
                y=[label],
                base=[pd.to_datetime(real_start)],
                orientation="h",
                marker_color=bar_color,
                marker_line_width=0,
                width=0.65,
            ))

    # Linha "hoje"
    fig.add_vline(
        x=pd.to_datetime(today).value / 1e6,
        line_dash="dot",
        line_color="#00afac",
        line_width=2,
        annotation_text="Hoje",
        annotation_font_color="#00afac",
        annotation_font_size=11,
    )

    fig.update_layout(
        barmode="overlay",
        height=max(200, len(tasks) * 44 + 80),
        xaxis=dict(type="date"),
        yaxis=dict(autorange="reversed"),
        showlegend=True,
    )
    dark_fig(fig)
    return fig


# ── Gate review card ──────────────────────────────────────────────────────────
def gate_card(gate: dict, compact: bool = False) -> dmc.Paper:
    status  = gate.get("status", "pending")
    color   = GATE_STATUS_COLORS.get(status, "gray")
    label   = gate.get("label", gate.get("gate_id", ""))
    descr   = gate.get("description", "")
    items   = gate.get("check_items", [])
    checked = sum(1 for c in items if c.get("checked"))

    style_map = {
        "pending":  {"border": "1px dashed #373A40"},
        "approved": {"border": "1px solid #2f9e44", "background": "rgba(47,158,68,.06)"},
        "rejected": {"border": "1px solid #fa5252", "background": "rgba(250,82,82,.06)"},
    }

    content = [
        dmc.Group(justify="space-between", children=[
            dmc.Text(label, fw=600, size="sm"),
            dmc.Badge(GATE_STATUS_LABELS.get(status, status), color=color, variant="light", size="xs"),
        ]),
        dmc.Text(descr, size="xs", c="dimmed"),
    ]

    if not compact and items:
        content.append(
            dmc.Text(f"✓ {checked}/{len(items)} itens verificados", size="xs", c=color, mt=4)
        )

    return dmc.Paper(
        p="sm",
        radius="md",
        style=style_map.get(status, {}),
        children=dmc.Stack(gap=4, children=content),
    )


# ── Sector color ──────────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "Software":    "blue",
    "Mecânica":    "orange",
    "Elétrica":    "yellow",
    "Automação":   "teal",
    "Integração":  "violet",
    "Design":      "pink",
    "Processos":   "cyan",
}

def sector_badge(sector: str) -> dmc.Badge:
    color = SECTOR_COLORS.get(sector, "gray")
    return dmc.Badge(sector, color=color, variant="light", size="sm")
