import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    res = await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )
    assert res.status_code == 201

    data = res.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "user"
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )
    res = await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "other@example.com",
            "password": "secret123",
        },
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )
    res = await client.post(
        "/api/auth/register",
        json={
            "username": "other",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client):
    res = await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "123",
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )

    res = await client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert res.status_code == 200

    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )

    res = await client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "wrong"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client):
    res = await client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "secret123"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_token(client):
    res = await client.get("/api/users/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client):
    await client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )

    login_res = await client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "secret123"},
    )
    token = login_res.json()["access_token"]

    res = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    data = res.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    res = await client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid_token_here"},
    )
    assert res.status_code == 401