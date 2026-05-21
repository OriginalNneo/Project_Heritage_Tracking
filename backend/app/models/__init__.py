from sqlalchemy import BigInteger, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

import enum


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    SKIPPED = "skipped"


class RaceStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"


class Team(Base):
    __tablename__ = "teams"

    chat_id = Column(BigInteger, primary_key=True)
    team_name = Column(String(255), nullable=False)
    current_checkpoint_id = Column(Integer, ForeignKey("checkpoints.checkpoint_id"), nullable=True)
    score = Column(Integer, default=0)
    status = Column(String(50), default=RaceStatus.NOT_STARTED.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="team", cascade="all, delete-orphan")
    current_checkpoint = relationship("Checkpoint", foreign_keys=[current_checkpoint_id])


class TeamMember(Base):
    __tablename__ = "team_members"

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("teams.chat_id"), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    team = relationship("Team", back_populates="members")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    checkpoint_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    target_radius = Column(Float, default=20.0)
    riddle_text = Column(Text, nullable=True)
    task_description = Column(Text, nullable=True)
    answer = Column(String(255), nullable=True)
    hint = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Submission(Base):
    __tablename__ = "submissions"

    sub_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(BigInteger, ForeignKey("teams.chat_id"), nullable=False, index=True)
    checkpoint_id = Column(Integer, ForeignKey("checkpoints.checkpoint_id"), nullable=False, index=True)
    submitted_answer = Column(String(255), nullable=True)
    status = Column(String(50), default=SubmissionStatus.PENDING.value)
    submitted_by = Column(BigInteger, nullable=True)
    image_path = Column(String(512), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    team = relationship("Team", back_populates="submissions")
    checkpoint = relationship("Checkpoint")


class LiveTelemetry(Base):
    __tablename__ = "live_telemetry"

    telemetry_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(BigInteger, ForeignKey("teams.chat_id"), nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
