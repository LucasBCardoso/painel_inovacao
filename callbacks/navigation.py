"""
Navigation + Auth callbacks — Painel TRL Delta
"""
from dash import Input, Output, State, callback, no_update, clientside_callback
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash import html
from werkzeug.security import check_password_hash
from database import db, User

# Pages (imported lazily to avoid circular imports)
def _load_page(pathname: str, user: dict | None):
    """Retorna o layout da página correspondente ao pathname."""
    is_admin = user and user.get("role") == "admin"

    # Rotas públicas / auth
    if not user:
        return _login_required()

    # Redireciona user comum para meu-painel
    if not is_admin and pathname not in ("/meu-painel", "/perfil", "/kanban"):
        from pages.user_dashboard import layout as user_dash_layout
        return user_dash_layout(user)

    route_map = {
        "/":              lambda: _dashboard_layout(user),
        "/kanban":        lambda: _kanban_layout(user),
        "/projetos":      lambda: _projects_layout(user),
        "/usuarios":      lambda: _users_layout(user),
        "/admin":         lambda: _admin_layout(user),
        "/calendario":    lambda: _calendar_layout(user),
        "/relatorio":     lambda: _report_layout(user),
        "/configuracoes": lambda: _settings_layout(user),
        "/meu-painel":    lambda: _user_dashboard_layout(user),
    }

    # Rota com parâmetro: /projetos/:id
    if pathname.startswith("/projetos/"):
        project_id = pathname.split("/projetos/")[1].rstrip("/")
        return _project_detail_layout(project_id, user)

    factory = route_map.get(pathname, lambda: _not_found())
    return factory()


def _login_required():
    return dmc.Center(
        h=300,
        children=dmc.Stack(align="center", gap="md", children=[
            dmc.ThemeIcon(
                size="xl", radius="xl", color="teal", variant="light",
                children=dmc.Text("🔒", size="xl"),
            ),
            dmc.Text("Faça login para acessar o sistema", size="lg", fw=600),
        ]),
    )


def _not_found():
    return dmc.Center(
        h=300,
        children=dmc.Stack(align="center", gap="md", children=[
            dmc.Text("404", size="3rem", fw=900, c="dimmed"),
            dmc.Text("Página não encontrada", size="lg"),
        ]),
    )


def _dashboard_layout(user):
    from pages.dashboard import layout
    return layout(user)

def _kanban_layout(user):
    from pages.kanban import layout
    return layout(user)

def _projects_layout(user):
    from pages.projects import layout
    return layout(user)

def _project_detail_layout(project_id, user):
    from pages.project_detail import layout
    return layout(project_id, user)

def _users_layout(user):
    from pages.users import layout
    return layout(user)

def _admin_layout(user):
    from pages.admin import layout
    return layout(user)

def _calendar_layout(user):
    from pages.calendar import layout
    return layout(user)

def _report_layout(user):
    from pages.report import layout
    return layout(user)

def _settings_layout(user):
    from pages.settings import layout
    return layout(user)

def _user_dashboard_layout(user):
    from pages.user_dashboard import layout
    return layout(user)


def register_navigation(app):

    # ── Login ─────────────────────────────────────────────────────────────────
    @app.callback(
        Output("auth-store",      "data"),
        Output("login-modal",     "opened"),
        Output("login-error",     "children"),
        Output("login-error",     "style"),
        Output("header-user-info","children"),
        Output("logout-btn",      "style"),
        Input("login-btn",        "n_clicks"),
        State("login-email",      "value"),
        State("login-password",   "value"),
        State("auth-store",       "data"),
        prevent_initial_call=True,
    )
    def do_login(n_clicks, email, password, current_auth):
        if not n_clicks:
            raise PreventUpdate
        if not email or not password:
            return (no_update, True,
                    "Preencha e-mail e senha", {"display": "block"},
                    no_update, no_update)

        user = User.query.filter_by(email=email.strip().lower(), is_active=True).first()
        if not user or not check_password_hash(user.password_hash, password):
            return (no_update, True,
                    "E-mail ou senha inválidos", {"display": "block"},
                    no_update, no_update)

        user_dict = user.to_dict()
        role_label = "Administrador" if user.role == "admin" else "Usuário"
        return (
            user_dict,
            False,
            "", {"display": "none"},
            f"{user.full_name} · {role_label}",
            {"display": "block"},
        )

    # ── Logout ────────────────────────────────────────────────────────────────
    @app.callback(
        Output("auth-store",       "data",    allow_duplicate=True),
        Output("login-modal",      "opened",  allow_duplicate=True),
        Output("header-user-info", "children",allow_duplicate=True),
        Output("logout-btn",       "style",   allow_duplicate=True),
        Input("logout-btn",        "n_clicks"),
        prevent_initial_call=True,
    )
    def do_logout(n):
        if not n:
            raise PreventUpdate
        return None, True, "", {"display": "none"}

    # ── Routing + NavLink highlight ───────────────────────────────────────────
    @app.callback(
        Output("page-content",         "children"),
        Output("nav-dashboard",        "active"),
        Output("nav-kanban",           "active"),
        Output("nav-projetos",         "active"),
        Output("nav-usuarios",         "active"),
        Output("nav-admin",            "active"),
        Output("nav-calendario",       "active"),
        Output("nav-relatorio",        "active"),
        Output("nav-configuracoes",    "active"),
        Output("nav-meu-painel",       "active"),
        Input("url",                   "pathname"),
        State("auth-store",            "data"),
    )
    def route(pathname, user):
        path = pathname or "/"
        page = _load_page(path, user)
        active = [path == p for p in [
            "/", "/kanban", "/projetos", "/usuarios", "/admin",
            "/calendario", "/relatorio", "/configuracoes", "/meu-painel",
        ]]
        return (page, *active)

    # ── Restore header info on page load ─────────────────────────────────────
    @app.callback(
        Output("login-modal",      "opened",  allow_duplicate=True),
        Output("header-user-info", "children",allow_duplicate=True),
        Output("logout-btn",       "style",   allow_duplicate=True),
        Input("url",               "pathname"),
        State("auth-store",        "data"),
        prevent_initial_call=True,
    )
    def restore_session(pathname, user):
        if user:
            role_label = "Administrador" if user.get("role") == "admin" else "Usuário"
            return False, f"{user.get('full_name','')} · {role_label}", {"display": "block"}
        return True, "", {"display": "none"}

    # ── Mobile burger ─────────────────────────────────────────────────────────
    @app.callback(
        Output("app-shell",  "navbar"),
        Input("burger-btn",  "opened"),
        State("app-shell",   "navbar"),
        prevent_initial_call=True,
    )
    def toggle_mobile_nav(opened, navbar):
        navbar["collapsed"] = {"mobile": not opened}
        return navbar
