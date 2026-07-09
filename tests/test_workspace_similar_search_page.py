"""Guardrails for the workspace Similar Search page wiring."""

from pathlib import Path

from tests.frontend_api_sources import api_client_source


def test_workspace_similar_search_page_uses_real_garment_photo_workflow() -> None:
    page_source = Path("apps/web/src/app/(workspace)/workspace/similar-search/page.tsx").read_text(encoding="utf-8")
    workflow_source = Path("apps/web/src/features/workspace/similar-search-workflow.tsx").read_text(encoding="utf-8")
    client_source = api_client_source()
    contracts_source = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")

    assert "SimilarSearchWorkflow" in page_source
    assert 'hasCapability("similar_search_create")' in workflow_source
    assert 'accept="image/jpeg,image/png,image/webp"' in workflow_source
    assert 'formData.append("garment_photo"' in workflow_source
    assert "searchSimilarByGarmentPhoto" in workflow_source
    assert "buildRedirectUrl" in workflow_source
    assert "/api/similar-search/redirect" in workflow_source
    assert "offer_url" in workflow_source
    assert "searchSimilarByGarmentPhoto" in client_source
    assert "recordSimilarSearchClick" in client_source
    assert "/api/similar-search/garment-photo" in client_source
    assert "/api/similar-search/events/click" in client_source
    assert "SimilarSearchResponse" in contracts_source
    assert "SimilarSearchClickEventResponse" in contracts_source
    assert "Пока backend" not in page_source
    assert "Посмотреть товар" in workflow_source
    assert "Товар в локальном каталоге" in workflow_source
    assert "Сейчас бесплатно ищем только по одобренной локальной базе магазинов" in workflow_source
    assert "Внешние маркетплейсы и Instagram подключим отдельным слоем" in workflow_source
    assert "Проверяем только товары, которые прошли админ-проверку" in workflow_source
    assert "Если ничего не найдено, это не ошибка оплаты и не списание credits" in workflow_source
    assert "Покажем сначала ближайшие магазины и доставку в ваш город" in workflow_source
    assert "Рџ" not in workflow_source
