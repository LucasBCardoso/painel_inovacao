"""
Database models - Painel TRL Delta
Sistema de Gestão de Projetos de Inovação por TRL
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timezone, timedelta
import json

db = SQLAlchemy()

_BRT = timezone(timedelta(hours=-3))

def now_brt():
    return datetime.now(_BRT).replace(tzinfo=None)


# ── Many-to-many helpers ──────────────────────────────────────────────────────
project_responsible = db.Table(
    "project_responsible",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("user_id",    db.Integer, db.ForeignKey("users.id"),    primary_key=True),
)

project_sectors = db.Table(
    "project_sectors",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("sector",     db.String(100), primary_key=True),
)

project_tags = db.Table(
    "project_tags",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("tag",        db.String(100), primary_key=True),
)

task_assigned = db.Table(
    "task_assigned",
    db.Column("task_id", db.Integer, db.ForeignKey("project_tasks.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"),         primary_key=True),
)

meeting_attendees = db.Table(
    "meeting_attendees",
    db.Column("meeting_id", db.Integer, db.ForeignKey("meetings.id"),   primary_key=True),
    db.Column("user_id",    db.Integer, db.ForeignKey("users.id"),       primary_key=True),
)


# ── User ──────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
    id                   = db.Column(db.Integer,     primary_key=True)
    full_name            = db.Column(db.String(150), nullable=False)
    email                = db.Column(db.String(200), unique=True, nullable=False)
    password_hash        = db.Column(db.String(256), nullable=False)
    role                 = db.Column(db.String(30),  default="user")      # admin | user
    position             = db.Column(db.String(150))
    avatar_color         = db.Column(db.String(30),  default="teal")
    is_active            = db.Column(db.Boolean,     default=True)
    must_change_password = db.Column(db.Boolean,     default=False)
    created_at           = db.Column(db.DateTime,    default=now_brt)

    # Relationships (back_populates on Project side)
    responsible_for = db.relationship("Project",   secondary=project_responsible, back_populates="responsible")
    comments        = db.relationship("ProjectComment", back_populates="author")
    history_entries = db.relationship("ProjectHistory", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id, "full_name": self.full_name, "email": self.email,
            "role": self.role, "position": self.position,
            "avatar_color": self.avatar_color, "is_active": self.is_active,
            "must_change_password": self.must_change_password,
        }


# ── Project ───────────────────────────────────────────────────────────────────
GATE_DEFINITIONS = {
    "gate1": {"label": "Gate 1 – TRL 3",  "trl_threshold": 3, "description": "Conceito → Desenvolvimento"},
    "gate2": {"label": "Gate 2 – TRL 6",  "trl_threshold": 6, "description": "Desenvolvimento → Industrialização"},
    "gate3": {"label": "Gate 3 – TRL 7",  "trl_threshold": 7, "description": "Prontidão Operacional"},
    "gate4": {"label": "Gate 4 – TRL 8+", "trl_threshold": 8, "description": "Escalabilidade"},
}

PRIORITY_COLORS = {"alta": "red", "media": "yellow", "baixa": "blue"}
TRL_COLORS = {
    1: "#6741d9", 2: "#7048e8", 3: "#7950f2",
    4: "#1971c2", 5: "#1c7ed6", 6: "#228be6",
    7: "#0ca678", 8: "#099268", 9: "#2f9e44",
}

class Project(db.Model):
    __tablename__ = "projects"
    id          = db.Column(db.Integer,     primary_key=True)
    name        = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    trl         = db.Column(db.Integer,     default=1)   # 1–9
    progress    = db.Column(db.Float,       default=0.0)
    priority    = db.Column(db.String(20),  default="media")  # alta | media | baixa
    folder_path = db.Column(db.String(500))
    project_tag = db.Column(db.String(100))
    start_date  = db.Column(db.Date)
    target_date = db.Column(db.Date)
    is_active   = db.Column(db.Boolean,  default=True)
    created_at  = db.Column(db.DateTime, default=now_brt)
    updated_at  = db.Column(db.DateTime, default=now_brt, onupdate=now_brt)

    responsible  = db.relationship("User",    secondary=project_responsible, back_populates="responsible_for")
    okrs         = db.relationship("TRLObjective", back_populates="project", cascade="all, delete-orphan", order_by="TRLObjective.trl_from")
    gate_reviews = db.relationship("GateReview",   back_populates="project", cascade="all, delete-orphan")
    tasks        = db.relationship("ProjectTask",   back_populates="project", cascade="all, delete-orphan", order_by="ProjectTask.deadline")
    comments     = db.relationship("ProjectComment",back_populates="project", cascade="all, delete-orphan", order_by="ProjectComment.created_at.desc()")
    meetings     = db.relationship("Meeting",       back_populates="project", cascade="all, delete-orphan", order_by="Meeting.meeting_date")
    attachments  = db.relationship("Attachment",    back_populates="project", cascade="all, delete-orphan")
    history      = db.relationship("ProjectHistory",back_populates="project", cascade="all, delete-orphan", order_by="ProjectHistory.timestamp.desc()")

    @property
    def sectors(self):
        from sqlalchemy import select
        rows = db.session.execute(
            select(project_sectors.c.sector).where(project_sectors.c.project_id == self.id)
        ).fetchall()
        return [r[0] for r in rows]

    @property
    def tags(self):
        rows = db.session.execute(
            db.select(project_tags.c.tag).where(project_tags.c.project_id == self.id)
        ).fetchall()
        return [r[0] for r in rows]

    @property
    def is_delayed(self):
        if not self.target_date: return False
        return date.today() > self.target_date and self.progress < 100

    @property
    def phase(self):
        if self.trl <= 3: return "Descoberta"
        if self.trl <= 6: return "Desenvolvimento"
        if self.trl <= 8: return "Industrialização"
        return "Concluído"

    def recalc_progress(self):
        """Recalcula progresso do projeto com base nos KRs (média ponderada)."""
        all_krs = []
        for okr in self.okrs:
            all_krs.extend(okr.key_results)
        if not all_krs:
            return
        total_weight = sum(kr.weight for kr in all_krs) or 1
        total_weighted = sum(kr.completion_pct * kr.weight for kr in all_krs)
        self.progress = round(total_weighted / total_weight, 1)

    def can_advance_trl(self):
        """Verifica se pode avançar TRL (gate aprovado, se necessário)."""
        gate_map = {"gate1": 3, "gate2": 6, "gate3": 7, "gate4": 8}
        for gate_id, threshold in gate_map.items():
            if self.trl == threshold:
                gate = next((g for g in self.gate_reviews if g.gate_id == gate_id), None)
                if gate and gate.status != "approved":
                    return False, f"Gate {gate_id} precisa ser aprovado antes"
        return True, ""

    def to_dict(self, include_relations=False):
        d = {
            "id": self.id, "name": self.name, "description": self.description,
            "trl": self.trl, "progress": self.progress, "priority": self.priority,
            "folder_path": self.folder_path, "project_tag": self.project_tag,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "is_active": self.is_active, "phase": self.phase,
            "is_delayed": self.is_delayed,
            "responsible": [u.to_dict() for u in self.responsible],
            "sectors": self.sectors, "tags": self.tags,
        }
        if include_relations:
            d["okrs"]         = [o.to_dict(include_krs=True) for o in self.okrs]
            d["gate_reviews"] = [g.to_dict() for g in self.gate_reviews]
            d["tasks"]        = [t.to_dict() for t in self.tasks]
            d["meetings"]     = [m.to_dict() for m in self.meetings]
            d["attachments"]  = [a.to_dict() for a in self.attachments]
            d["history"]      = [h.to_dict() for h in self.history[:50]]
        return d


# ── TRL Objective / OKR ───────────────────────────────────────────────────────
class TRLObjective(db.Model):
    __tablename__ = "trl_objectives"
    id         = db.Column(db.Integer,     primary_key=True)
    project_id = db.Column(db.Integer,     db.ForeignKey("projects.id"), nullable=False)
    trl_from   = db.Column(db.Integer,     nullable=False)
    trl_to     = db.Column(db.Integer,     nullable=False)
    objective  = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.Date)
    end_date   = db.Column(db.Date)

    project     = db.relationship("Project",   back_populates="okrs")
    key_results = db.relationship("KeyResult", back_populates="objective", cascade="all, delete-orphan")

    def to_dict(self, include_krs=False):
        d = {"id": self.id, "project_id": self.project_id,
             "trl_from": self.trl_from, "trl_to": self.trl_to,
             "objective": self.objective,
             "start_date": self.start_date.isoformat() if self.start_date else None,
             "end_date": self.end_date.isoformat() if self.end_date else None}
        if include_krs:
            d["key_results"] = [kr.to_dict(include_subtasks=True) for kr in self.key_results]
        return d


# ── Key Result ────────────────────────────────────────────────────────────────
class KeyResult(db.Model):
    __tablename__ = "key_results"
    id           = db.Column(db.Integer,     primary_key=True)
    objective_id = db.Column(db.Integer,     db.ForeignKey("trl_objectives.id"), nullable=False)
    description  = db.Column(db.String(500), nullable=False)
    weight       = db.Column(db.Float,       default=1.0)
    evidence     = db.Column(db.Text)
    evidence_url = db.Column(db.String(500))

    objective = db.relationship("TRLObjective", back_populates="key_results")
    subtasks  = db.relationship("KRSubtask",    back_populates="key_result", cascade="all, delete-orphan")

    @property
    def completion_pct(self):
        if not self.subtasks: return 0.0
        total = len(self.subtasks)
        done  = sum(1 for s in self.subtasks if s.completed)
        return round((done / total) * 100, 1) if total else 0.0

    def to_dict(self, include_subtasks=False):
        d = {"id": self.id, "objective_id": self.objective_id,
             "description": self.description, "weight": self.weight,
             "evidence": self.evidence, "evidence_url": self.evidence_url,
             "completion_pct": self.completion_pct}
        if include_subtasks:
            d["subtasks"] = [s.to_dict() for s in self.subtasks]
        return d


# ── KR Subtask ────────────────────────────────────────────────────────────────
class KRSubtask(db.Model):
    __tablename__ = "kr_subtasks"
    id           = db.Column(db.Integer,     primary_key=True)
    key_result_id= db.Column(db.Integer,     db.ForeignKey("key_results.id"), nullable=False)
    description  = db.Column(db.String(500), nullable=False)
    completed    = db.Column(db.Boolean,     default=False)
    completed_at = db.Column(db.DateTime)
    created_at   = db.Column(db.DateTime,    default=now_brt)

    key_result = db.relationship("KeyResult", back_populates="subtasks")

    def to_dict(self):
        return {"id": self.id, "key_result_id": self.key_result_id,
                "description": self.description, "completed": self.completed,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None}


# ── Gate Review ───────────────────────────────────────────────────────────────
class GateReview(db.Model):
    __tablename__ = "gate_reviews"
    id          = db.Column(db.Integer,    primary_key=True)
    project_id  = db.Column(db.Integer,    db.ForeignKey("projects.id"), nullable=False)
    gate_id     = db.Column(db.String(20), nullable=False)   # gate1 | gate2 | gate3 | gate4
    status      = db.Column(db.String(20), default="pending") # pending | approved | rejected
    review_date = db.Column(db.Date)
    reviewer    = db.Column(db.String(200))
    notes       = db.Column(db.Text)
    observation = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=now_brt)

    project     = db.relationship("Project",        back_populates="gate_reviews")
    check_items = db.relationship("GateCheckItem",  cascade="all, delete-orphan")
    comments    = db.relationship("GateComment",    cascade="all, delete-orphan")

    def to_dict(self):
        defn = GATE_DEFINITIONS.get(self.gate_id, {})
        return {
            "id": self.id, "project_id": self.project_id, "gate_id": self.gate_id,
            "status": self.status, "notes": self.notes, "observation": self.observation,
            "review_date": self.review_date.isoformat() if self.review_date else None,
            "reviewer": self.reviewer,
            "label": defn.get("label", self.gate_id),
            "description": defn.get("description", ""),
            "check_items": [c.to_dict() for c in self.check_items],
            "comments": [c.to_dict() for c in self.comments],
        }


class GateCheckItem(db.Model):
    __tablename__ = "gate_check_items"
    id      = db.Column(db.Integer,    primary_key=True)
    gate_id = db.Column(db.Integer,    db.ForeignKey("gate_reviews.id"), nullable=False)
    text    = db.Column(db.String(500),nullable=False)
    checked = db.Column(db.Boolean,    default=False)

    def to_dict(self):
        return {"id": self.id, "gate_id": self.gate_id, "text": self.text, "checked": self.checked}


class GateComment(db.Model):
    __tablename__ = "gate_comments"
    id         = db.Column(db.Integer,  primary_key=True)
    gate_id    = db.Column(db.Integer,  db.ForeignKey("gate_reviews.id"), nullable=False)
    text       = db.Column(db.Text,     nullable=False)
    author_id  = db.Column(db.Integer,  db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=now_brt)
    author     = db.relationship("User", foreign_keys=[author_id])

    def to_dict(self):
        return {"id": self.id, "text": self.text,
                "author": self.author.full_name if self.author else "Sistema",
                "created_at": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else ""}


# ── Project Task ──────────────────────────────────────────────────────────────
class ProjectTask(db.Model):
    __tablename__ = "project_tasks"
    id               = db.Column(db.Integer,    primary_key=True)
    project_id       = db.Column(db.Integer,    db.ForeignKey("projects.id"), nullable=False)
    title            = db.Column(db.String(300),nullable=False)
    description      = db.Column(db.Text)
    priority         = db.Column(db.String(20), default="media")
    trl_level        = db.Column(db.Integer)
    gate_id          = db.Column(db.String(20))
    kr_id            = db.Column(db.Integer,    db.ForeignKey("key_results.id"))
    estimated_start  = db.Column(db.Date)
    estimated_end    = db.Column(db.Date)
    start_date       = db.Column(db.Date)
    deadline         = db.Column(db.Date)
    actual_start     = db.Column(db.Date)
    actual_end       = db.Column(db.Date)
    completed_at     = db.Column(db.DateTime)
    status_override  = db.Column(db.String(30))   # manual override: pending|in_progress|completed|delayed
    created_at       = db.Column(db.DateTime,   default=now_brt)

    project          = db.relationship("Project",      back_populates="tasks")
    items            = db.relationship("TaskItem",      cascade="all, delete-orphan")
    deadline_changes = db.relationship("TaskDeadlineChange", cascade="all, delete-orphan",
                                       order_by="TaskDeadlineChange.changed_at")
    assigned_users   = db.relationship("User", secondary=task_assigned)

    @property
    def computed_status(self):
        if self.status_override:
            return self.status_override
        if self.completed_at or (self.items and all(i.checked for i in self.items)):
            return "completed"
        if self.deadline and date.today() > self.deadline:
            return "delayed"
        if self.actual_start or self.start_date:
            return "in_progress"
        return "pending"

    @property
    def is_delayed(self):
        return self.computed_status == "delayed"

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id, "title": self.title,
            "description": self.description, "priority": self.priority,
            "trl_level": self.trl_level, "gate_id": self.gate_id, "kr_id": self.kr_id,
            "estimated_start": self.estimated_start.isoformat() if self.estimated_start else None,
            "estimated_end": self.estimated_end.isoformat() if self.estimated_end else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.computed_status, "is_delayed": self.is_delayed,
            "assigned_users": [u.to_dict() for u in self.assigned_users],
            "items": [i.to_dict() for i in self.items],
            "deadline_changes": [c.to_dict() for c in self.deadline_changes],
        }


class TaskItem(db.Model):
    __tablename__ = "task_items"
    id          = db.Column(db.Integer,     primary_key=True)
    task_id     = db.Column(db.Integer,     db.ForeignKey("project_tasks.id"), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    checked     = db.Column(db.Boolean,     default=False)

    def to_dict(self):
        return {"id": self.id, "task_id": self.task_id, "description": self.description, "checked": self.checked}


class TaskDeadlineChange(db.Model):
    __tablename__ = "task_deadline_changes"
    id            = db.Column(db.Integer,    primary_key=True)
    task_id       = db.Column(db.Integer,    db.ForeignKey("project_tasks.id"), nullable=False)
    previous_date = db.Column(db.Date)
    new_date      = db.Column(db.Date)
    reason        = db.Column(db.String(200))
    note          = db.Column(db.Text)
    changed_at    = db.Column(db.DateTime,   default=now_brt)
    changed_by_id = db.Column(db.Integer,    db.ForeignKey("users.id"))
    changed_by    = db.relationship("User",  foreign_keys=[changed_by_id])

    def to_dict(self):
        return {
            "id": self.id, "task_id": self.task_id,
            "previous_date": self.previous_date.isoformat() if self.previous_date else None,
            "new_date": self.new_date.isoformat() if self.new_date else None,
            "reason": self.reason, "note": self.note,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "changed_by": self.changed_by.full_name if self.changed_by else "Sistema",
        }


# ── Meeting ───────────────────────────────────────────────────────────────────
class Meeting(db.Model):
    __tablename__ = "meetings"
    id           = db.Column(db.Integer,     primary_key=True)
    project_id   = db.Column(db.Integer,     db.ForeignKey("projects.id"), nullable=False)
    title        = db.Column(db.String(300), nullable=False)
    meeting_date = db.Column(db.Date,        nullable=False)
    meeting_time = db.Column(db.String(10))
    duration     = db.Column(db.Integer)    # minutos
    notes        = db.Column(db.Text)
    location     = db.Column(db.String(300))
    created_at   = db.Column(db.DateTime,   default=now_brt)

    project   = db.relationship("Project", back_populates="meetings")
    attendees = db.relationship("User", secondary=meeting_attendees)

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id, "title": self.title,
            "meeting_date": self.meeting_date.isoformat() if self.meeting_date else None,
            "meeting_time": self.meeting_time, "duration": self.duration,
            "notes": self.notes, "location": self.location,
            "attendees": [u.to_dict() for u in self.attendees],
        }


# ── Attachment ────────────────────────────────────────────────────────────────
class Attachment(db.Model):
    __tablename__ = "attachments"
    id          = db.Column(db.Integer,     primary_key=True)
    project_id  = db.Column(db.Integer,     db.ForeignKey("projects.id"), nullable=False)
    name        = db.Column(db.String(300), nullable=False)
    file_type   = db.Column(db.String(30),  default="document")  # document|image|video|link|folder
    url         = db.Column(db.String(1000),nullable=False)
    description = db.Column(db.Text)
    trl_level   = db.Column(db.Integer)
    kr_id       = db.Column(db.Integer, db.ForeignKey("key_results.id"))
    added_at    = db.Column(db.DateTime, default=now_brt)

    project = db.relationship("Project", back_populates="attachments")

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id, "name": self.name,
            "file_type": self.file_type, "url": self.url, "description": self.description,
            "trl_level": self.trl_level, "kr_id": self.kr_id,
            "added_at": self.added_at.strftime("%d/%m/%Y") if self.added_at else "",
        }


# ── Project Comment ───────────────────────────────────────────────────────────
class ProjectComment(db.Model):
    __tablename__ = "project_comments"
    id         = db.Column(db.Integer,  primary_key=True)
    project_id = db.Column(db.Integer,  db.ForeignKey("projects.id"), nullable=False)
    text       = db.Column(db.Text,     nullable=False)
    author_id  = db.Column(db.Integer,  db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=now_brt)

    project = db.relationship("Project", back_populates="comments")
    author  = db.relationship("User",    back_populates="comments")

    def to_dict(self):
        return {
            "id": self.id, "text": self.text, "project_id": self.project_id,
            "author": self.author.full_name if self.author else "Sistema",
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "",
        }


# ── Project History ───────────────────────────────────────────────────────────
class ProjectHistory(db.Model):
    __tablename__ = "project_history"
    id          = db.Column(db.Integer,     primary_key=True)
    project_id  = db.Column(db.Integer,     db.ForeignKey("projects.id"), nullable=False)
    event_type  = db.Column(db.String(80),  nullable=False)
    description = db.Column(db.Text,         nullable=False)
    timestamp   = db.Column(db.DateTime,    default=now_brt)
    user_id     = db.Column(db.Integer,     db.ForeignKey("users.id"))

    project = db.relationship("Project", back_populates="history")
    user    = db.relationship("User",    back_populates="history_entries")

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id,
            "event_type": self.event_type, "description": self.description,
            "timestamp": self.timestamp.strftime("%d/%m/%Y %H:%M") if self.timestamp else "",
            "user": self.user.full_name if self.user else "Sistema",
        }


# ── System Config (tags, settings) ───────────────────────────────────────────
class SystemConfig(db.Model):
    __tablename__ = "system_config"
    key   = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)

    @classmethod
    def get(cls, key, default=None):
        row = cls.query.get(key)
        return json.loads(row.value) if row else default

    @classmethod
    def set(cls, key, value):
        row = cls.query.get(key)
        if row:
            row.value = json.dumps(value)
        else:
            db.session.add(cls(key=key, value=json.dumps(value)))
        db.session.commit()
