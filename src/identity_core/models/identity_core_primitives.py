"""Shared identity core model primitives."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class LeadLifecycleState(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    MERGED = "merged"
    DELETED = "deleted"


class ChannelIdentityState(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class IdentityBindingState(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class ContactPointType(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    TELEGRAM_HANDLE = "telegram_handle"
    OTHER = "other"


class ContactPointVerificationState(StrEnum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REVOKED = "revoked"


class SharedUsePolicy(StrEnum):
    SINGLE_OWNER = "single_owner"
    ALLOWED_WITH_REVIEW = "allowed_with_review"
    SHARED_ALLOWED = "shared_allowed"


class RecoveryTokenState(StrEnum):
    ISSUED = "issued"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"


class CandidateConfidenceClass(StrEnum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class CandidateReviewState(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AuditDecisionType(StrEnum):
    LINK_CREATED = "link_created"
    LINK_REVOKED = "link_revoked"
    BINDING_SUPERSEDED = "binding_superseded"
    CANDIDATE_ACCEPTED = "candidate_accepted"
    CANDIDATE_REJECTED = "candidate_rejected"
    RECOVERY_ISSUED = "recovery_issued"
    RECOVERY_CONSUMED = "recovery_consumed"
    MERGE_DECISION = "merge_decision"


@dataclass(slots=True, frozen=True)
class EntityTimestamp:
    created_at: datetime
    updated_at: datetime


JsonMap = dict[str, Any]
LeadId = UUID
ChannelIdentityId = UUID
IdentityBindingId = UUID
ContactPointId = UUID
RecoveryTokenId = UUID
IdentityCandidateId = UUID
AuditEventId = UUID
