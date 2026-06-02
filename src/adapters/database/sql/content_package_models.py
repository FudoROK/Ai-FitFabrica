"""Portable SQLAlchemy models for content-package workflow persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class ContentPackageJobRow(SqlBase):
    """Canonical content-package job aggregate root row."""

    __tablename__ = "content_package_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_card_version_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    package_name: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_channels_csv: Mapped[str] = mapped_column("requested_channels", Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ContentPackageVersionRow(SqlBase):
    """Generated content-package version stored separately from the job root."""

    __tablename__ = "content_package_versions"

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("content_package_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    package_name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ContentPackageArtifactRow(SqlBase):
    """One persisted artifact reference belonging to one generated package version."""

    __tablename__ = "content_package_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("content_package_versions.version_id", ondelete="CASCADE"), nullable=False, index=True)
    asset_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_content_package_jobs_status_created_at", ContentPackageJobRow.status, ContentPackageJobRow.created_at)
Index("ix_content_package_versions_job_id_created_at", ContentPackageVersionRow.job_id, ContentPackageVersionRow.created_at)
