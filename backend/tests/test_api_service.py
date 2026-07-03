import pytest

from app.services.api_service import APIService


@pytest.mark.asyncio
async def test_search_internet_returns_empty_when_dependency_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Search should degrade gracefully when DuckDuckGo support is unavailable."""
    service = APIService()
    service.set_internet_enabled(True)

    monkeypatch.setattr("app.services.api_service.DDGS", None, raising=False)

    results = await service.search_internet("test query")

    assert results == []
