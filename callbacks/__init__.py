"""
Callbacks registry — Painel TRL Delta
"""
from .navigation          import register_navigation
from .dashboard_cb        import register_dashboard
from .kanban_cb           import register_kanban
from .projects_cb         import register_projects
from .project_detail_cb   import register_projects_detail
from .users_cb            import register_users
from .admin_cb            import register_admin
from .calendar_cb          import register_calendar
from .report_cb            import register_report
from .settings_cb          import register_settings
from .user_dashboard_cb    import register_user_dashboard


def register_callbacks(app):
    register_navigation(app)
    register_dashboard(app)
    register_kanban(app)
    register_projects(app)
    register_projects_detail(app)
    register_users(app)
    register_admin(app)
    register_calendar(app)
    register_report(app)
    register_settings(app)
    register_user_dashboard(app)
