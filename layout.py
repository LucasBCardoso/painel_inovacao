"""
Layout — Painel TRL Delta
AppShell com sidebar, header e modal de login
"""
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify


def icon(name, size=18, color=None):
    return DashIconify(icon=name, width=size, color=color)


# ── TRL phase labels ──────────────────────────────────────────────────────────
TRL_PHASE = {
    "Descoberta":      list(range(1, 4)),
    "Desenvolvimento": list(range(4, 7)),
    "Industrialização":list(range(7, 10)),
}


def _nav(label, href, icon_name, nav_id, color=None):
    kwargs = {"color": color} if color else {}
    return dmc.NavLink(
        label=label,
        leftSection=icon(icon_name),
        id=f"nav-{nav_id}",
        href=href,
        variant="subtle",
        **kwargs,
    )


def create_navbar():
    return dmc.AppShellNavbar(
        p="sm",
        style={"borderRight": "1px solid #373A40"},
        children=[
            dmc.Stack(gap="xs", children=[
                # ── Geral ────────────────────────────────────────────────────
                _nav("Visão Geral",   "/",          "tabler:dashboard",        "dashboard"),
                _nav("Kanban TRL",    "/kanban",    "tabler:layout-kanban",    "kanban"),
                _nav("Projetos",      "/projetos",  "tabler:folder",           "projetos"),
                dmc.Divider(my="xs"),

                # ── Admin ─────────────────────────────────────────────────────
                dmc.Text("Administração", size="xs", c="dimmed",
                         style={"paddingLeft": "12px", "textTransform": "uppercase",
                                "letterSpacing": "0.06em"}),
                _nav("Usuários",      "/usuarios",      "tabler:users",        "usuarios"),
                _nav("Admin",         "/admin",          "tabler:list-check",   "admin"),
                _nav("Calendário",    "/calendario",     "tabler:calendar",     "calendario"),
                _nav("Relatórios",    "/relatorio",      "tabler:report",       "relatorio"),
                _nav("Configurações", "/configuracoes",  "tabler:settings",     "configuracoes"),
                dmc.Divider(my="xs"),

                # ── Meu Painel (só user) ───────────────────────────────────
                _nav("Meu Painel",    "/meu-painel",     "tabler:user",         "meu-painel", "cyan"),
            ])
        ],
    )


def create_header():
    return dmc.AppShellHeader(
        px="md",
        style={"background": "#1A1B1E", "borderBottom": "2px solid #00afac"},
        children=[
            dmc.Flex(
                align="center", justify="space-between", h="100%",
                children=[
                    dmc.Flex(align="center", gap="sm", children=[
                        dmc.Burger(id="burger-btn", hiddenFrom="sm", size="sm", color="white"),
                        dmc.Group(gap="sm", align="center", children=[
                            html.Img(
                                src="/assets/logo.png",
                                style={"height": "42px", "objectFit": "contain"},
                                id="header-logo",
                            ),
                            dmc.Divider(orientation="vertical",
                                        style={"height": "28px", "borderColor": "#373A40"}),
                            dmc.Stack(gap=0, children=[
                                dmc.Text("PAINEL TRL", fw=800, size="sm", c="white",
                                         style={"letterSpacing": "0.06em"}),
                                dmc.Text("Gestão de Inovação · Delta Máquinas Têxteis",
                                         size="xs", style={"color": "#00afac"}),
                            ]),
                        ]),
                    ]),
                    dmc.Group(gap="md", children=[
                        # Badges de fase rápida
                        dmc.Group(gap="xs", visibleFrom="md", children=[
                            dmc.Badge("Descoberta",       color="violet", variant="light", size="sm"),
                            dmc.Badge("Desenvolvimento",  color="blue",   variant="light", size="sm"),
                            dmc.Badge("Industrialização", color="green",  variant="light", size="sm"),
                        ]),
                        dmc.Text(id="header-user-info", size="sm", c="dimmed"),
                        dmc.ActionIcon(
                            id="logout-btn",
                            variant="subtle",
                            color="gray",
                            children=icon("tabler:logout", 18),
                            style={"display": "none"},
                        ),
                    ]),
                ],
            )
        ],
    )


def create_login_modal():
    return dmc.Modal(
        id="login-modal",
        title=dmc.Group(gap="sm", children=[
            icon("tabler:lock", 22, "#00afac"),
            dmc.Text("Acesso ao Sistema", fw=700, size="lg"),
        ]),
        opened=True,
        centered=True,
        withCloseButton=False,
        closeOnClickOutside=False,
        closeOnEscape=False,
        size="sm",
        children=[
            dmc.Stack(gap="md", children=[
                dmc.TextInput(
                    id="login-email",
                    label="E-mail",
                    placeholder="seu@email.com",
                    leftSection=icon("tabler:mail", 16),
                    required=True,
                ),
                dmc.PasswordInput(
                    id="login-password",
                    label="Senha",
                    placeholder="••••••",
                    leftSection=icon("tabler:lock", 16),
                    required=True,
                ),
                dmc.Alert(
                    id="login-error",
                    color="red",
                    icon=icon("tabler:alert-circle", 20),
                    style={"display": "none"},
                    children="",
                ),
                dmc.Button(
                    "Entrar",
                    id="login-btn",
                    fullWidth=True,
                    leftSection=icon("tabler:login", 18),
                    size="md",
                ),
                dmc.Text(
                    "Delta Máquinas Têxteis · Sistema de Gestão de P&D",
                    size="xs", c="dimmed", ta="center",
                ),
            ])
        ],
    )


def create_app_shell(page_content):
    return dmc.AppShell(
        [
            create_header(),
            create_navbar(),
            dmc.AppShellMain(
                children=[
                    html.Div(id="page-content", style={"padding": "20px"}),
                ]
            ),
            create_login_modal(),
        ],
        header={"height": 60},
        navbar={
            "width": 220,
            "breakpoint": "sm",
            "collapsed": {"mobile": True},
        },
        padding="0",
        id="app-shell",
    )
