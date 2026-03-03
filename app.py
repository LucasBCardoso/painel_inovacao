"""
Painel TRL Delta — Sistema de Gestão de Inovação
Delta Máquinas Têxteis
"""
import os
import dash
import dash_mantine_components as dmc
from dash import dcc, html
from flask import Flask
from sqlalchemy import text
from database import db
from layout import create_app_shell
from callbacks import register_callbacks
from seed_data import seed_database

# ── Flask + SQLAlchemy ────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
_DB   = os.path.join(_BASE, "instance", "painel_trl.db")
os.makedirs(os.path.join(_BASE, "instance"), exist_ok=True)

server = Flask(__name__)
server.config["SQLALCHEMY_DATABASE_URI"]        = f"sqlite:///{_DB}"
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
server.secret_key = "delta-trl-2026-secret"
db.init_app(server)

with server.app_context():
    db.create_all()
    seed_database(server)

# ── Dash App ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    title="Painel TRL · Delta Máquinas Têxteis",
    update_title=None,
)

# ── Tema Mantine (alinhado com PAINEL-RAMA) ───────────────────────────────────
_THEME = {
    "primaryColor": "teal",
    "primaryShade": 5,
    "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    "defaultRadius": "md",
    "colors": {
        "teal": [
            "#e6f7f7", "#b3e8e8", "#80d9d8", "#4dcac9",
            "#26bfbe", "#00afac", "#009b98", "#008a87",
            "#007370", "#005c5a",
        ],
        "dark": [
            "#C1C2C5", "#A6A7AB", "#909296", "#5c5f66",
            "#373A40", "#2C2E33", "#25262b", "#1A1B1E",
            "#141517", "#101113",
        ],
    },
    "components": {
        "Card":   {"defaultProps": {"shadow": "sm"}},
        "Paper":  {"defaultProps": {"shadow": "xs"}},
        "Button": {"defaultProps": {"color": "teal"}},
        "Badge":  {"defaultProps": {"color": "teal"}},
    },
}

app.layout = dmc.MantineProvider(
    id="mantine-provider",
    forceColorScheme="dark",
    theme=_THEME,
    children=[
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="auth-store",      storage_type="session"),
        dcc.Store(id="project-trigger", data=0),   # disparado ao mudar projeto
        dcc.Store(id="task-trigger",    data=0),   # disparado ao mudar tarefa
        create_app_shell(html.Div(id="page-content")),
    ],
)

register_callbacks(app)

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import socket
    try:
        _ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        _ip = "0.0.0.0"
    print("\n" + "=" * 60)
    print("  Painel TRL — Delta Máquinas Têxteis")
    print(f"  Local:  http://localhost:8051")
    print(f"  Rede:   http://{_ip}:8051")
    print(f"  Nginx:  http://inovacao.delta.local")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=8051, debug=False)
