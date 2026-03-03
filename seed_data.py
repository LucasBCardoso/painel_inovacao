"""
Seed data — Painel TRL Delta
Dados iniciais: usuários, projetos, OKRs, KRs, gates, tarefas
"""
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from database import (
    db, User, Project, TRLObjective, KeyResult, KRSubtask,
    GateReview, GateCheckItem, ProjectTask, TaskItem, Meeting,
    ProjectHistory, SystemConfig, project_sectors, project_responsible, task_assigned
)

# Paleta de cores dos avatares
AVATAR_COLORS = ["teal", "blue", "violet", "cyan", "green", "orange", "red", "grape"]

SECTORS = ["Software", "Mecânica", "Elétrica", "Automação", "Integração", "Design", "Processos"]


def seed_database(app):
    with app.app_context():
        if User.query.first():
            return  # já semeado

        print("🌱 [SEED] Populando banco de dados inicial…")

        # ── Usuários ──────────────────────────────────────────────────────────
        users = [
            User(full_name="Administrador Delta", email="admin@delta.com",
                 password_hash=generate_password_hash("admin123"),
                 role="admin", position="Gerente de P&D", avatar_color="teal"),
            User(full_name="João Silva", email="joao@delta.com",
                 password_hash=generate_password_hash("user123"),
                 role="user", position="Engenheiro de Software", avatar_color="blue"),
            User(full_name="Maria Souza", email="maria@delta.com",
                 password_hash=generate_password_hash("user123"),
                 role="user", position="Engenheira Mecânica", avatar_color="violet"),
            User(full_name="Pedro Oliveira", email="pedro@delta.com",
                 password_hash=generate_password_hash("user123"),
                 role="user", position="Engenheiro Elétrico", avatar_color="cyan"),
            User(full_name="Ana Costa", email="ana@delta.com",
                 password_hash=generate_password_hash("user123"),
                 role="user", position="Especialista em Automação", avatar_color="green"),
            User(full_name="Carlos Nunes", email="carlos@delta.com",
                 password_hash=generate_password_hash("user123"),
                 role="user", position="Engenheiro de Integração", avatar_color="orange"),
        ]
        for u in users:
            db.session.add(u)
        db.session.flush()

        admin_user = users[0]
        today = date.today()

        # ── Helper: adiciona setores ao projeto ───────────────────────────────
        def add_sectors(proj_id, sectors_list):
            for s in sectors_list:
                db.session.execute(
                    project_sectors.insert().values(project_id=proj_id, sector=s)
                )

        def add_responsible(proj_id, user_ids):
            for uid in user_ids:
                db.session.execute(
                    project_responsible.insert().values(project_id=proj_id, user_id=uid)
                )

        # ── Helper: gera OKRs padrão por TRL ─────────────────────────────────
        def generate_okrs_for_project(project):
            trl = project.trl
            okr_templates = {
                (1, 2): ("Validar conceito e viabilidade técnica básica",
                         ["Levantamento de requisitos concluído", "Estudo de viabilidade aprovado",
                          "Tecnologias candidatas identificadas", "Documento de conceito criado"]),
                (2, 3): ("Desenvolver e validar prova de conceito",
                         ["PoC funcional implementada", "Testes de laboratório realizados",
                          "Resultados documentados", "Viabilidade técnica confirmada"]),
                (3, 4): ("Demonstrar funcionalidade em ambiente simulado",
                         ["Protótipo funcional construído", "Testes em ambiente controlado",
                          "Desempenho mínimo alcançado", "Gate 1 aprovado"]),
                (4, 5): ("Validar tecnologia em ambiente relevante",
                         ["Integração de subsistemas realizada", "Testes em ambiente representativo",
                          "Requisitos de desempenho atendidos", "Documentação técnica atualizada"]),
                (5, 6): ("Demonstrar sistema integrado em ambiente relevante",
                         ["Sistema totalmente integrado e testado", "Performance validada",
                          "Análise de riscos concluída", "Gate 2 aprovado"]),
                (6, 7): ("Validar sistema em ambiente operacional",
                         ["Protótipo de pré-produção testado", "Testes em campo realizados",
                          "Normas e regulamentações verificadas", "Gate 3 aprovado"]),
                (7, 8): ("Completar e qualificar o sistema",
                         ["Sistema qualificado para produção", "Processos de fabricação definidos",
                          "Testes de aceitação realizados", "Gate 4 aprovado"]),
                (8, 9): ("Provar o sistema em ambiente operacional",
                         ["Sistema testado em escala plena", "Processo produtivo validado",
                          "Escalabilidade confirmada", "Entrega final aprovada"]),
            }
            phase_key = (trl, trl + 1) if trl < 9 else (8, 9)
            objective_text, subtask_texts = okr_templates.get(phase_key, okr_templates[(1, 2)])

            okr = TRLObjective(
                project_id=project.id,
                trl_from=phase_key[0], trl_to=phase_key[1],
                objective=objective_text,
                start_date=project.start_date,
                end_date=project.target_date,
            )
            db.session.add(okr)
            db.session.flush()

            kr = KeyResult(
                objective_id=okr.id,
                description=f"Cumprir todos os requisitos de entrega TRL {phase_key[1]}",
                weight=1.0,
            )
            db.session.add(kr)
            db.session.flush()

            for st_text in subtask_texts:
                db.session.add(KRSubtask(key_result_id=kr.id, description=st_text, completed=False))

            return okr, kr

        # ── Helper: cria gate reviews para um projeto ─────────────────────────
        def create_gate_reviews(project):
            gate_checklists = {
                "gate1": [
                    "Documento de conceito aprovado pela liderança",
                    "Viabilidade técnica confirmada",
                    "Cronograma preliminar definido",
                    "Riscos iniciais mapeados",
                ],
                "gate2": [
                    "Protótipo funcional desenvolvido e testado",
                    "Desempenho técnico mínimo demonstrado",
                    "Análise de mercado e impacto realizada",
                    "Plano de desenvolvimento aprovado",
                ],
                "gate3": [
                    "Sistema validado em campo",
                    "Conformidade com normas verificada",
                    "Plano de industrialização elaborado",
                    "Análise financeira de produção aprovada",
                ],
                "gate4": [
                    "Processo produtivo validado em escala",
                    "Testes de aceitação formais concluídos",
                    "Documentação técnica completa",
                    "Aprovação final da diretoria",
                ],
            }
            for gate_id, checklist in gate_checklists.items():
                gate = GateReview(
                    project_id=project.id,
                    gate_id=gate_id,
                    status="pending",
                )
                db.session.add(gate)
                db.session.flush()
                for item_text in checklist:
                    db.session.add(GateCheckItem(gate_id=gate.id, text=item_text, checked=False))

        # ── Projetos ──────────────────────────────────────────────────────────
        projects_data = [
            {
                "name": "Rama Têxtil 4.0",
                "description": "Automação avançada da máquina de rama têxtil com integração IoT, visão computacional e controlo preditivo.",
                "trl": 5, "priority": "alta",
                "sectors": ["Software", "Automação", "Integração"],
                "responsible_ids": [users[0].id, users[1].id],
                "start_date": today - timedelta(days=180),
                "target_date": today + timedelta(days=120),
                "project_tag": "RAMA-4.0",
                "tasks_data": [
                    ("Definir arquitetura IoT", "media", -60, 20, users[1].id),
                    ("Desenvolvimento módulo visão", "alta", -30, 45, users[1].id),
                    ("Testes de integração campo", "alta", 30, 90, users[4].id),
                ],
            },
            {
                "name": "Revisadeira REV1000 IA",
                "description": "Sistema de revisão de tecidos com inteligência artificial para detecção automática de defeitos.",
                "trl": 3, "priority": "alta",
                "sectors": ["Software", "Mecânica"],
                "responsible_ids": [users[1].id, users[2].id],
                "start_date": today - timedelta(days=90),
                "target_date": today + timedelta(days=210),
                "project_tag": "REV1000-IA",
                "tasks_data": [
                    ("Coleta e anotação de dataset", "alta", -30, 30, users[1].id),
                    ("Treino do modelo de detecção", "alta", 10, 60, users[1].id),
                    ("Integração com hardware da revisadeira", "media", 60, 120, users[2].id),
                ],
            },
            {
                "name": "Relaxadeira RLX600 II",
                "description": "Segunda geração da relaxadeira com controle de tensão aprimorado e redução de consumo energético em 30%.",
                "trl": 7, "priority": "media",
                "sectors": ["Mecânica", "Elétrica"],
                "responsible_ids": [users[2].id, users[3].id],
                "start_date": today - timedelta(days=300),
                "target_date": today + timedelta(days=60),
                "project_tag": "RLX600-II",
                "tasks_data": [
                    ("Validação em campo — cliente piloto", "alta", -15, 30, users[2].id),
                    ("Documentação técnica final", "media", 15, 45, users[3].id),
                    ("Aprovação Gate 3", "alta", 45, 60, users[0].id),
                ],
            },
            {
                "name": "Sistema de Exaustão Inteligente",
                "description": "Controle adaptativo de exaustão com sensores de qualidade do ar e ajuste automático de vazão.",
                "trl": 2, "priority": "media",
                "sectors": ["Automação", "Elétrica"],
                "responsible_ids": [users[4].id, users[3].id],
                "start_date": today - timedelta(days=30),
                "target_date": today + timedelta(days=300),
                "project_tag": "EXA-INT",
                "tasks_data": [
                    ("Levantamento de requisitos técnicos", "media", -15, 15, users[4].id),
                    ("Seleção de sensores e atuadores", "media", 15, 45, users[3].id),
                    ("PoC em bancada de testes", "alta", 60, 120, users[4].id),
                ],
            },
            {
                "name": "Painel Elétrico Modular",
                "description": "Plataforma modular de painéis elétricos com barramentos configuráveis para diferentes linhas de produção.",
                "trl": 6, "priority": "baixa",
                "sectors": ["Elétrica", "Processos"],
                "responsible_ids": [users[3].id, users[5].id],
                "start_date": today - timedelta(days=240),
                "target_date": today + timedelta(days=90),
                "project_tag": "PAIN-MOD",
                "tasks_data": [
                    ("Validação normativa NR-12", "alta", -20, 20, users[3].id),
                    ("Fabricação lote piloto", "media", 20, 70, users[5].id),
                    ("Testes de qualificação", "alta", 70, 90, users[3].id),
                ],
            },
            {
                "name": "Motor Alta Eficiência MAE-300",
                "description": "Motor elétrico de alta eficiência energética IE4 para aplicações têxteis, com redução de 25% no consumo.",
                "trl": 4, "priority": "alta",
                "sectors": ["Elétrica", "Mecânica"],
                "responsible_ids": [users[3].id, users[2].id],
                "start_date": today - timedelta(days=120),
                "target_date": today + timedelta(days=180),
                "project_tag": "MAE-300",
                "tasks_data": [
                    ("Prototipagem do núcleo magnético", "alta", -40, 20, users[2].id),
                    ("Testes de eficiência em bancada", "alta", 10, 60, users[3].id),
                    ("Ajustes de geometria", "media", 60, 120, users[2].id),
                ],
            },
        ]

        for pd in projects_data:
            proj = Project(
                name=pd["name"],
                description=pd["description"],
                trl=pd["trl"],
                priority=pd["priority"],
                start_date=pd["start_date"],
                target_date=pd["target_date"],
                project_tag=pd["project_tag"],
                progress=0.0,
            )
            db.session.add(proj)
            db.session.flush()

            add_sectors(proj.id, pd["sectors"])
            add_responsible(proj.id, pd["responsible_ids"])

            # OKRs + KRs
            okr, kr = generate_okrs_for_project(proj)

            # Gates
            create_gate_reviews(proj)

            # Tarefas
            for task_title, task_prio, start_offset, end_offset, task_user_id in pd["tasks_data"]:
                task = ProjectTask(
                    project_id=proj.id,
                    title=task_title,
                    priority=task_prio,
                    trl_level=proj.trl,
                    start_date=today + timedelta(days=start_offset),
                    deadline=today + timedelta(days=end_offset),
                    kr_id=kr.id,
                )
                db.session.add(task)
                db.session.flush()
                db.session.execute(
                    task_assigned.insert().values(task_id=task.id, user_id=task_user_id)
                )

            # Recalcula progresso
            db.session.flush()
            proj.recalc_progress()

            # Histórico
            db.session.add(ProjectHistory(
                project_id=proj.id,
                event_type="project_created",
                description=f'Projeto "{proj.name}" criado',
                user_id=admin_user.id,
            ))

        # ── System Config ─────────────────────────────────────────────────────
        db.session.add(SystemConfig(
            key="system_tags",
            value='["IoT", "Machine Learning", "Automação", "Inovação", "Eficiência Energética", "Mecatrônica", "Indústria 4.0", "Visão Computacional"]'
        ))
        db.session.add(SystemConfig(
            key="trl_documentation",
            value='"TRL 1 — Princípios básicos observados; TRL 2 — Conceito tecnológico formulado; TRL 3 — Prova de conceito experimental; TRL 4 — Tecnologia validada em laboratório; TRL 5 — Tecnologia validada em ambiente relevante; TRL 6 — Tecnologia demonstrada em ambiente relevante; TRL 7 — Demonstração de protótipo em ambiente operacional; TRL 8 — Sistema completo e qualificado; TRL 9 — Sistema comprovado em ambiente operacional."'
        ))

        db.session.commit()
        print("✅ [SEED] Banco de dados populado com sucesso.")
        print("   Acesso admin: admin@delta.com / admin123")
        print("   Acesso user:  joao@delta.com  / user123\n")
