from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.garment_taxonomy import GarmentTaxonomyCandidate, GarmentTaxonomyCandidateStatus
from src.entrypoints.admin_taxonomy_routes import router


class _TaxonomyService:
    def __init__(self) -> None:
        self.candidates = [
            GarmentTaxonomyCandidate(
                id="candidate-1",
                proposed_code="kimono jacket",
                proposed_display_name="Kimono jacket",
                proposed_category="outerwear",
                confidence=0.74,
                agent_reasoning_summary="Open lightweight outerwear layer.",
            )
        ]
        self.approved: list[tuple[str, str]] = []
        self.rejected: list[tuple[str, str, str]] = []
        self.merged: list[tuple[str, str, str]] = []
        self.renamed: list[tuple[str, str, str, str]] = []

    async def list_candidates(self, *, status=GarmentTaxonomyCandidateStatus.PENDING_REVIEW):
        return [candidate for candidate in self.candidates if candidate.status == status]

    async def approve_candidate(self, *, candidate_id: str, actor_id: str):
        self.approved.append((candidate_id, actor_id))
        return self.candidates[0].approve(actor_id=actor_id, approved_catalog_item_code="kimono_jacket")

    async def reject_candidate(self, *, candidate_id: str, actor_id: str, review_reason: str):
        self.rejected.append((candidate_id, actor_id, review_reason))
        return self.candidates[0].reject(actor_id=actor_id, review_reason=review_reason)

    async def merge_candidate(self, *, candidate_id: str, actor_id: str, target_catalog_item_code: str):
        self.merged.append((candidate_id, actor_id, target_catalog_item_code))
        return self.candidates[0].model_copy(
            update={
                "status": GarmentTaxonomyCandidateStatus.MERGED,
                "reviewed_by": actor_id,
                "approved_catalog_item_code": target_catalog_item_code,
            }
        )

    async def rename_and_approve_candidate(
        self,
        *,
        candidate_id: str,
        actor_id: str,
        approved_catalog_item_code: str,
        approved_display_name: str,
    ):
        self.renamed.append((candidate_id, actor_id, approved_catalog_item_code, approved_display_name))
        return self.candidates[0].model_copy(
            update={
                "status": GarmentTaxonomyCandidateStatus.APPROVED,
                "reviewed_by": actor_id,
                "approved_catalog_item_code": approved_catalog_item_code,
                "proposed_display_name": approved_display_name,
            }
        )


class _FailingTaxonomyService(_TaxonomyService):
    async def merge_candidate(self, *, candidate_id: str, actor_id: str, target_catalog_item_code: str):
        raise ValueError("target taxonomy item 'missing' does not exist")


def _client(*, enabled: bool, monkeypatch, service: _TaxonomyService | None = None) -> TestClient:
    app = FastAPI()
    app.state.settings = SimpleNamespace(
        enable_admin_taxonomy=enabled,
        admin_api_token="test-admin-token",
        allow_unsafe_admin_header_auth=False,
    )
    app.include_router(router)
    if service is not None:
        monkeypatch.setattr(
            "src.entrypoints.admin_taxonomy_routes.garment_taxonomy_service",
            lambda settings: service,
        )
    return TestClient(app)


def _headers() -> dict[str, str]:
    return {"authorization": "Bearer test-admin-token"}


def test_admin_taxonomy_routes_are_disabled_by_default(monkeypatch) -> None:
    client = _client(enabled=False, service=_TaxonomyService(), monkeypatch=monkeypatch)

    response = client.get("/api/admin/taxonomy/candidates", headers=_headers())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "admin_taxonomy_disabled"


def test_admin_taxonomy_routes_require_admin_role(monkeypatch) -> None:
    client = _client(enabled=True, service=_TaxonomyService(), monkeypatch=monkeypatch)

    response = client.get("/api/admin/taxonomy/candidates")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_auth_invalid"


def test_admin_taxonomy_lists_candidates(monkeypatch) -> None:
    client = _client(enabled=True, service=_TaxonomyService(), monkeypatch=monkeypatch)

    response = client.get("/api/admin/taxonomy/candidates", headers=_headers())

    assert response.status_code == 200
    assert response.json()["candidates"][0]["id"] == "candidate-1"


def test_admin_taxonomy_approve_reject_and_merge(monkeypatch) -> None:
    service = _TaxonomyService()
    client = _client(enabled=True, service=service, monkeypatch=monkeypatch)

    approve = client.post("/api/admin/taxonomy/candidates/candidate-1/approve", headers=_headers())
    reject = client.post(
        "/api/admin/taxonomy/candidates/candidate-1/reject",
        headers=_headers(),
        json={"review_reason": "Too broad."},
    )
    merge = client.post(
        "/api/admin/taxonomy/candidates/candidate-1/merge",
        headers=_headers(),
        json={"target_catalog_item_code": "shirt"},
    )

    assert approve.status_code == 200
    assert approve.json()["candidate"]["status"] == "approved"
    assert reject.status_code == 200
    assert reject.json()["candidate"]["status"] == "rejected"
    assert merge.status_code == 200
    assert merge.json()["candidate"]["status"] == "merged"
    assert service.approved == [("candidate-1", "admin-api-token")]
    assert service.rejected == [("candidate-1", "admin-api-token", "Too broad.")]
    assert service.merged == [("candidate-1", "admin-api-token", "shirt")]


def test_admin_taxonomy_rename_and_approve(monkeypatch) -> None:
    service = _TaxonomyService()
    client = _client(enabled=True, service=service, monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/taxonomy/candidates/candidate-1/rename-and-approve",
        headers=_headers(),
        json={
            "approved_catalog_item_code": "kimono_jacket",
            "approved_display_name": "Kimono Jacket",
        },
    )

    assert response.status_code == 200
    assert response.json()["candidate"]["status"] == "approved"
    assert service.renamed == [("candidate-1", "admin-api-token", "kimono_jacket", "Kimono Jacket")]


def test_admin_taxonomy_validation_errors_are_structured(monkeypatch) -> None:
    client = _client(enabled=True, service=_FailingTaxonomyService(), monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/taxonomy/candidates/candidate-1/merge",
        headers=_headers(),
        json={"target_catalog_item_code": "missing"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "admin_taxonomy_validation_failed"
    assert "target taxonomy item" in response.json()["error"]["message"]


def test_admin_taxonomy_routes_report_storage_unavailable(monkeypatch) -> None:
    client = _client(enabled=True, service=None, monkeypatch=monkeypatch)
    monkeypatch.setattr(
        "src.entrypoints.admin_taxonomy_routes.garment_taxonomy_service",
        lambda settings: None,
    )

    response = client.get("/api/admin/taxonomy/candidates", headers=_headers())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "admin_taxonomy_storage_unavailable"
