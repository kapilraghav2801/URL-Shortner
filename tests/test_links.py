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


@pytest.mark.asyncio
async def test_create_link_with_expiration(client):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "link_with_expiration",
            "expires_at": "2030-01-01T00:00:00Z",
        },
    )
    assert create_response.status_code == 201
    data = create_response.json()

    assert data["expires_at"] == "2030-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_update_link_expiration(client):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "update_expiration",
        },
    )

    assert create_response.status_code == 201

    update_response = await client.patch(
        "/api/v1/links/update_expiration",
        json={
            "expires_at": "2030-01-01T00:00:00Z",
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["short_code"] == "update_expiration"
    assert data["expires_at"] == "2030-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_deactivate_link(client):

    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "deactivate-test",
        },
    )

    assert create_response.status_code == 201

    update_response = await client.patch(
        "/api/v1/links/deactivate-test",
        json={
            "is_active": False,
        },
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["is_active"] is False

    redirect_response = await client.get(
        "/deactivate-test",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 404
    assert redirect_response.json()["detail"] == "Link is inactive"


@pytest.mark.asyncio
async def test_update_link_remove_expiration(client):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "remove-expiration",
            "expires_at": "2030-01-01T00:00:00Z",
        },
    )

    assert create_response.status_code == 201

    update_response = await client.patch(
        "/api/v1/links/remove-expiration",
        json={
            "expires_at": None,
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["expires_at"] is None


@pytest.mark.asyncio
async def test_update_unknown_link_returns_not_found(client):
    response = await client.patch(
        "/api/v1/links/does-not-exist",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found"


@pytest.mark.asyncio
async def test_create_link_generates_short_code(client):
    response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["short_code"] is not None
    assert len(data["short_code"]) == 7


@pytest.mark.asyncio
async def test_link_analytics_returns_time_based_counts(
    client,
    test_session_factory,
):
    create_response = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "time-analytics",
        },
    )

    assert create_response.status_code == 201

    link_id = create_response.json()["id"]

    now = datetime.now(UTC)

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    week_start = today_start - timedelta(days=today_start.weekday())

    month_start = today_start.replace(day=1)

    async with test_session_factory() as session:
        events = [
            ClickEvent(
                link_id=link_id,
                clicked_at=now,
            ),
            ClickEvent(
                link_id=link_id,
                clicked_at=week_start + timedelta(hours=1),
            ),
            ClickEvent(
                link_id=link_id,
                clicked_at=month_start + timedelta(hours=1),
            ),
            ClickEvent(
                link_id=link_id,
                clicked_at=month_start - timedelta(hours=1),
            ),
        ]

        session.add_all(events)
        await session.commit()

    response = await client.get(
        "/api/v1/links/time-analytics/analytics",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["short_code"] == "time-analytics"
    assert data["total_clicks"] == 4
    assert data["clicks_today"] == 1
    assert data["clicks_this_week"] == 2
    assert data["clicks_this_month"] == 3


@pytest.mark.asyncio
async def test_list_links(client):
    await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com",
            "short_code": "list-link-one",
        },
    )

    await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://google.com",
            "short_code": "list-link-two",
        },
    )

    response = await client.get(
        "/api/v1/links",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    short_codes = {link["short_code"] for link in data}

    assert short_codes == {
        "list-link-one",
        "list-link-two",
    }
