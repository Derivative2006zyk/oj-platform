import pytest


async def _make_user(client, username: str, email: str, role: str = "user"):
    """注册一个用户，直接改 DB 设 role。"""
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "secret123"},
    )
    # 通过 SQL 修改 role（测试里用 admin key 或其他方式都不行）
    # 改用 fixture 提供的 db 直接改
    from app.database import async_session
    from app.models.user import User
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one()
        user.role = role
        await db.commit()


async def _login(client, username: str) -> str:
    res = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "secret123"},
    )
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_list_users_requires_admin(client):
    await _make_user(client, "normal", "normal@example.com")
    token = await _login(client, "normal")

    res = await client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_list_users_as_admin(client):
    await _make_user(client, "admin1", "admin1@example.com", role="admin")
    await _make_user(client, "user1", "user1@example.com")
    await _make_user(client, "user2", "user2@example.com")

    token = await _login(client, "admin1")

    res = await client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_users_filter_by_role(client):
    await _make_user(client, "admin1", "admin1@example.com", role="admin")
    await _make_user(client, "user1", "user1@example.com")

    token = await _login(client, "admin1")

    res = await client.get(
        "/api/admin/users?role=admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["total"] == 1


@pytest.mark.asyncio
async def test_change_role(client):
    await _make_user(client, "admin1", "admin1@example.com", role="admin")
    await _make_user(client, "user1", "user1@example.com")

    token = await _login(client, "admin1")

    # 查 user1 的 id
    res = await client.get(
        "/api/admin/users?keyword=user1",
        headers={"Authorization": f"Bearer {token}"},
    )
    uid = res.json()["items"][0]["id"]

    # 改成 admin
    res = await client.put(
        f"/api/admin/users/{uid}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_cannot_change_own_role(client):
    await _make_user(client, "admin1", "admin1@example.com", role="admin")
    token = await _login(client, "admin1")

    res = await client.get(
        "/api/admin/users?keyword=admin1",
        headers={"Authorization": f"Bearer {token}"},
    )
    uid = res.json()["items"][0]["id"]

    res = await client.put(
        f"/api/admin/users/{uid}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "user"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_ban_and_unban(client):
    await _make_user(client, "admin1", "admin1@example.com", role="admin")
    await _make_user(client, "user1", "user1@example.com")

    token = await _login(client, "admin1")

    res = await client.get(
        "/api/admin/users?keyword=user1",
        headers={"Authorization": f"Bearer {token}"},
    )
    uid = res.json()["items"][0]["id"]

    # 封禁
    res = await client.put(
        f"/api/admin/users/{uid}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # 被封禁用户无法登录
    res = await client.post(
        "/api/auth/login",
        json={"username": "user1", "password": "secret123"},
    )
    assert res.status_code == 401

    # 解封
    res = await client.put(
        f"/api/admin/users/{uid}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": True},
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is True

    # 再次登录成功
    res = await client.post(
        "/api/auth/login",
        json={"username": "user1", "password": "secret123"},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_cannot_ban_self(client):
    await _make_user(client, "admin1", "admin1@example.com", role="admin")
    token = await _login(client, "admin1")

    res = await client.get(
        "/api/admin/users?keyword=admin1",
        headers={"Authorization": f"Bearer {token}"},
    )
    uid = res.json()["items"][0]["id"]

    res = await client.put(
        f"/api/admin/users/{uid}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_admin_stats(client):
    await _make_user(client, "admin1", "admin1@example.com", role="admin")
    token = await _login(client, "admin1")

    res = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_users"] == 1
    assert data["total_admins"] == 1
    assert data["active_users"] == 1
    assert data["banned_users"] == 0