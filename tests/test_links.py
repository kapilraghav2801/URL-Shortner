from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.click_event import ClickEvent
from app.models.link import Link
from app.repositories.click_event import ClickEventRepository


@pytest.mark.asyncio
async def test_create_link(client):
    response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "example",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["short_code"] == "example"
    assert data["destination_url"] == "https://example.com/"
    assert data["is_active"] is True
    assert data["expires_at"] is None


@pytest.mark.asyncio
async def test_duplicate_short_code_returns_conflict(client):
    payload = {
        "destination_url": "https://example.com",
        "short_code": "duplicate",
    }

    first_response = await client.post(
        "/api/v1/links",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/links",
        json=payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Short code already exists"


@pytest.mark.asyncio
async def test_invalid_destination_url_returns_unprocessable_entity(client):
    response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "not-a-url",
            "short_code": "invalid-url",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_redirect_existing_link(client):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "redirect-me",
        },
    )

    assert create_response.status_code == 201

    redirect_response = await client.get(
        "/redirect-me",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/"


@pytest.mark.asyncio
async def test_redirect_unknown_short_code_returns_not_found(client):
    response = await client.get(
        "/does-not-exist",
        follow_redirects=False,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.asyncio
async def test_redirect_records_click_event(client, test_session_factory):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "analytics-test",
        },
    )

    assert create_response.status_code == 201

    data = create_response.json()
    link_id = data["id"]

    redirect_response = await client.get(
        "/analytics-test",
        headers={
            "user-agent": "TestBrowser/1.0",
            "referer": "https://google.com",
        },
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307

    async with test_session_factory() as session:
        result = await session.execute(
            select(ClickEvent).where(ClickEvent.link_id == link_id)
        )

        event = result.scalar_one()

    assert event.link_id == link_id
    assert event.ip_address == "127.0.0.1"
    assert event.user_agent == "TestBrowser/1.0"
    assert event.referrer == "https://google.com"
    assert event.clicked_at is not None


@pytest.mark.asyncio
async def test_inactive_link_returns_not_found(
    client,
    test_session_factory,
):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "inactive-test",
        },
    )

    assert create_response.status_code == 201

    data = create_response.json()
    link_id = data["id"]

    async with test_session_factory() as session:
        result = await session.execute(select(Link).where(Link.id == link_id))

        link = result.scalar_one()

        link.is_active = False

        await session.commit()

    response = await client.get(
        "/inactive-test",
        follow_redirects=False,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_expired_link_returns_not_found(
    client,
    test_session_factory,
):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "inactive-test",
        },
    )

    assert create_response.status_code == 201

    data = create_response.json()
    link_id = data["id"]

    async with test_session_factory() as session:
        result = await session.execute(select(Link).where(Link.id == link_id))
        link = result.scalar_one()

        link.expires_at = datetime.now(UTC) - timedelta(days=1)

        await session.commit()

        response = await client.get(
            "/inactive-test",
            follow_redirects=False,
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_count_click_events_by_link_id(
    client,
    test_session_factory,
):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "count-test",
        },
    )

    assert create_response.status_code == 201

    data = create_response.json()
    link_id = data["id"]

    async with test_session_factory() as session:
        event1 = ClickEvent(link_id=link_id)
        event2 = ClickEvent(link_id=link_id)
        event3 = ClickEvent(link_id=link_id)

        session.add_all(
            [
                event1,
                event2,
                event3,
            ]
        )

        await session.commit()

        repository = ClickEventRepository(session)

        count = await repository.count_by_link_id(link_id)

    assert count == 3


@pytest.mark.asyncio
async def test_link_analytics_returns_click_count(client):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "analytics-count",
        },
    )

    assert create_response.status_code == 201

    await client.get(
        "/analytics-count",
        follow_redirects=False,
    )

    await client.get(
        "/analytics-count",
        follow_redirects=False,
    )

    await client.get(
        "/analytics-count",
        follow_redirects=False,
    )

    analytics_response = await client.get(
        "/api/v1/links/analytics-count/analytics",
    )

    assert analytics_response.status_code == 200

    data = analytics_response.json()

    assert data["short_code"] == "analytics-count"
    assert data["total_clicks"] == 3


@pytest.mark.asyncio
async def test_link_analytics_unknown_short_code_returns_not_found(client):
    response = await client.get(
        "/api/v1/links/does-not-exist/analytics",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"
