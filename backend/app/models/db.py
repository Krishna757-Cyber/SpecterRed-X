"""SQLAlchemy 2.0 ORM models and database bootstrap.

SQLite file-backed so history survives restarts. The schema is created at
startup and a schema-version row is recorded. No Alembic (per the two-hour
constraint and because the repo did not previously use it).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SchemaInfo(Base):
    __tablename__ = "schema_info"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(32), ForeignKey("scenarios.id"), nullable=False)
    scenario_version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="baseline")  # baseline|replay
    baseline_run_id: Mapped[str | None] = mapped_column(String(40), ForeignKey("runs.id"), nullable=True)
    initial_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    final_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="completed")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    events: Mapped[list["Event"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="Event.seq"
    )
    decisions: Mapped[list["AgentDecision"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="AgentDecision.seq"
    )


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(40), ForeignKey("runs.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    step_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[Run] = relationship(back_populates="events")


class AgentDecision(Base):
    __tablename__ = "agent_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(40), ForeignKey("runs.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    decision_id: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[Run] = relationship(back_populates="decisions")


class Comparison(Base):
    __tablename__ = "comparisons"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    baseline_run_id: Mapped[str] = mapped_column(String(40), ForeignKey("runs.id"), nullable=False)
    replay_run_id: Mapped[str] = mapped_column(String(40), ForeignKey("runs.id"), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(40), ForeignKey("runs.id"), nullable=False)
    comparison_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


_settings = get_settings()
_engine = create_engine(
    _settings.database_url,
    connect_args={"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def get_engine():
    return _engine


def init_db() -> None:
    """Create tables, record schema version and seed scenario definitions."""
    Base.metadata.create_all(_engine)
    from app.simulation import scenarios as scen

    with SessionLocal() as db:
        if db.scalar(select(SchemaInfo).limit(1)) is None:
            db.add(SchemaInfo(version=_settings.schema_version))
        # Upsert scenario definitions (idempotent on version_hash).
        for sc in scen.all_scenarios():
            existing = db.get(Scenario, sc["id"])
            if existing is None:
                db.add(
                    Scenario(
                        id=sc["id"],
                        version=sc["version"],
                        version_hash=sc["version_hash"],
                        title=sc["title"],
                        definition=sc,
                    )
                )
            elif existing.version_hash != sc["version_hash"]:
                existing.version = sc["version"]
                existing.version_hash = sc["version_hash"]
                existing.title = sc["title"]
                existing.definition = sc
        db.commit()
