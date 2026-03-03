"""
Users callbacks — Painel TRL Delta
"""
from dash import Input, Output, State, ALL, ctx, no_update, html
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from werkzeug.security import generate_password_hash
from database import db, User, Project, ProjectTask
from callbacks.helpers import icon, user_avatar, progress_bar


def _user_card(u: User, projects: list[Project], is_admin: bool) -> dmc.Paper:
    # Count tasks
    user_tasks = ProjectTask.query.filter(
        ProjectTask.assigned_users.any(id=u.id)
    ).all()
    total   = len(user_tasks)
    done    = sum(1 for t in user_tasks if t.computed_status == "completed")
    delayed = sum(1 for t in user_tasks if t.computed_status == "delayed")
    pct     = round(done / total * 100, 0) if total else 0.0

    user_projs = [p for p in projects if any(r.id == u.id for r in p.responsible)]

    return dmc.Paper(
        p="md", radius="md",
        children=dmc.Stack(gap="sm", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Group(gap="sm", children=[
                    user_avatar(u.to_dict(), 40),
                    dmc.Stack(gap=0, children=[
                        dmc.Text(u.full_name, fw=600, size="sm"),
                        dmc.Text(u.position or u.email, size="xs", c="dimmed"),
                    ]),
                ]),
                dmc.Group(gap="xs", children=[
                    dmc.Badge("Admin" if u.role == "admin" else "User",
                              color="teal" if u.role == "admin" else "gray",
                              variant="light", size="xs"),
                    dmc.ActionIcon(
                        id={"type": "user-edit-btn", "user_id": u.id},
                        variant="subtle", size="sm",
                        children=icon("tabler:pencil", 14),
                        style={"display": "block" if is_admin else "none"},
                    ),
                ]),
            ]),
            dmc.Divider(),
            dmc.SimpleGrid(cols=3, spacing="xs", children=[
                dmc.Stack(gap=0, align="center", children=[
                    dmc.Text(str(total),   fw=700, size="lg"),
                    dmc.Text("Tarefas",    size="xs", c="dimmed"),
                ]),
                dmc.Stack(gap=0, align="center", children=[
                    dmc.Text(str(done),    fw=700, size="lg", c="green"),
                    dmc.Text("Conc.",      size="xs", c="dimmed"),
                ]),
                dmc.Stack(gap=0, align="center", children=[
                    dmc.Text(str(delayed), fw=700, size="lg",
                             c="red" if delayed else "dimmed"),
                    dmc.Text("Atras.",     size="xs", c="dimmed"),
                ]),
            ]),
            progress_bar(pct),
            dmc.Group(gap=4, children=[
                dmc.Badge(p.name[:20], size="xs", variant="outline", color="teal")
                for p in user_projs[:3]
            ] or [dmc.Text("—", size="xs", c="dimmed")]),
        ]),
    )


def _user_form(u: User | None = None, error: str = "") -> dmc.Stack:
    return dmc.Stack(gap="md", children=[
        dmc.TextInput(
            id="user-form-name", label="Nome Completo",
            value=u.full_name if u else "",
            required=True, leftSection=icon("tabler:user", 16),
        ),
        dmc.TextInput(
            id="user-form-email", label="E-mail",
            value=u.email if u else "", type="email",
            required=True, leftSection=icon("tabler:mail", 16),
        ),
        dmc.TextInput(
            id="user-form-position", label="Cargo",
            value=u.position or "" if u else "",
            leftSection=icon("tabler:briefcase", 16),
        ),
        dmc.Select(
            id="user-form-role", label="Perfil",
            value=u.role if u else "user",
            data=[{"value": "admin", "label": "Administrador"},
                  {"value": "user",  "label": "Usuário"}],
        ),
        dmc.Select(
            id="user-form-color", label="Cor do Avatar",
            value=u.avatar_color if u else "teal",
            data=[
                {"value": "teal",   "label": "Teal"},
                {"value": "blue",   "label": "Azul"},
                {"value": "violet", "label": "Violeta"},
                {"value": "cyan",   "label": "Ciano"},
                {"value": "green",  "label": "Verde"},
                {"value": "orange", "label": "Laranja"},
                {"value": "red",    "label": "Vermelho"},
            ],
        ),
        dmc.PasswordInput(
            id="user-form-password",
            label="Senha" + (" (deixe vazio para manter)" if u else ""),
            leftSection=icon("tabler:lock", 16),
        ),
        dmc.Alert(error, color="red", id="user-form-error",
                  style={"display": "block" if error else "none"}),
        dmc.Group(justify="flex-end", gap="sm", children=[
            dmc.Button("Cancelar", id="user-form-cancel",
                       variant="subtle", color="gray"),
            dmc.Button("Salvar",   id="user-form-save",
                       leftSection=icon("tabler:check", 16)),
        ]),
    ])


def register_users(app):

    @app.callback(
        Output("users-grid", "children"),
        Input("url",          "pathname"),
        State("auth-store",   "data"),
    )
    def render_users(pathname, user):
        if pathname != "/usuarios" or not user:
            raise PreventUpdate
        users    = User.query.filter_by(is_active=True).order_by(User.full_name).all()
        projects = Project.query.filter_by(is_active=True).all()
        is_admin = user.get("role") == "admin"

        if not users:
            return dmc.Text("Nenhum usuário", c="dimmed", ta="center", py="xl")

        return dmc.SimpleGrid(
            cols={"base": 1, "sm": 2, "md": 3},
            spacing="md",
            children=[_user_card(u, projects, is_admin) for u in users],
        )

    @app.callback(
        Output("user-modal",       "opened"),
        Output("user-modal-title", "children"),
        Output("user-modal-body",  "children"),
        Output("editing-user-id",  "data"),
        Input("user-new-btn",      "n_clicks"),
        Input({"type": "user-edit-btn", "user_id": ALL}, "n_clicks"),
        State("auth-store", "data"),
        prevent_initial_call=True,
    )
    def open_user_modal(new_click, edit_clicks, user):
        if not user or user.get("role") != "admin":
            raise PreventUpdate

        triggered = ctx.triggered_id

        if triggered == "user-new-btn":
            return (
                True,
                dmc.Group(gap="sm", children=[icon("tabler:user-plus", 18, "#00afac"),
                                              dmc.Text("Novo Usuário", fw=700)]),
                _user_form(),
                None,
            )

        if isinstance(triggered, dict) and triggered.get("type") == "user-edit-btn":
            uid = triggered["user_id"]
            u = User.query.get(uid)
            if not u:
                raise PreventUpdate
            return (
                True,
                dmc.Group(gap="sm", children=[icon("tabler:pencil", 18, "#00afac"),
                                              dmc.Text(f"Editar — {u.full_name}", fw=700)]),
                _user_form(u),
                uid,
            )

        raise PreventUpdate

    @app.callback(
        Output("user-modal", "opened", allow_duplicate=True),
        Output("users-grid", "children", allow_duplicate=True),
        Output("user-form-error", "children", allow_duplicate=True),
        Output("user-form-error", "style",    allow_duplicate=True),
        Input("user-form-save",   "n_clicks"),
        State("user-form-name",   "value"),
        State("user-form-email",  "value"),
        State("user-form-position","value"),
        State("user-form-role",   "value"),
        State("user-form-color",  "value"),
        State("user-form-password","value"),
        State("editing-user-id",  "data"),
        State("auth-store",       "data"),
        prevent_initial_call=True,
    )
    def save_user(n, name, email, position, role, color, password, editing_id, user):
        if not n or not user or user.get("role") != "admin":
            raise PreventUpdate

        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not name or not email:
            return no_update, no_update, "Nome e e-mail são obrigatórios", {"display": "block"}

        if editing_id:
            u = User.query.get(int(editing_id))
            if not u:
                raise PreventUpdate
            u.full_name   = name
            u.email       = email
            u.position    = position or ""
            u.role        = role or "user"
            u.avatar_color= color or "teal"
            if password:
                u.password_hash = generate_password_hash(password)
        else:
            if not password:
                return no_update, no_update, "Senha é obrigatória para novo usuário", {"display": "block"}
            if User.query.filter_by(email=email).first():
                return no_update, no_update, "E-mail já cadastrado", {"display": "block"}
            u = User(
                full_name=name, email=email, position=position or "",
                role=role or "user", avatar_color=color or "teal",
                password_hash=generate_password_hash(password),
            )
            db.session.add(u)

        db.session.commit()

        projects = Project.query.filter_by(is_active=True).all()
        is_admin = user.get("role") == "admin"
        users    = User.query.filter_by(is_active=True).order_by(User.full_name).all()
        grid     = dmc.SimpleGrid(
            cols={"base": 1, "sm": 2, "md": 3}, spacing="md",
            children=[_user_card(u2, projects, is_admin) for u2 in users],
        )
        return False, grid, "", {"display": "none"}

    @app.callback(
        Output("user-modal", "opened", allow_duplicate=True),
        Input("user-form-cancel", "n_clicks"),
        prevent_initial_call=True,
    )
    def cancel_user(_):
        return False
