"""核心接口的端到端测试：用户、新闻、缓存失效、收藏/历史、同步鉴权、AI 兜底与限流。"""

import uuid

import pytest

pytestmark = pytest.mark.anyio

PASSWORD = "Passw0rd!123"


async def _register_and_login(client, username=None):
    username = username or f"u_{uuid.uuid4().hex[:10]}"
    register = await client.post(
        "/api/user/register", json={"username": username, "password": PASSWORD}
    )
    assert register.status_code == 200, register.text
    login = await client.post(
        "/api/user/login", json={"username": username, "password": PASSWORD}
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["token"]
    return username, {"Authorization": token}


async def _publish_news(client, auth, title, category_id=8):
    response = await client.post(
        "/api/news/upload",
        data={
            "title": title,
            "content": "这是一条用于自动化测试的新闻正文，长度超过十个字符。",
            "categoryId": str(category_id),
            "description": "自动化测试新闻",
        },
        headers=auth,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


async def test_register_login_and_user_info(client):
    username, auth = await _register_and_login(client)

    info = await client.get("/api/user/info", headers=auth)
    assert info.status_code == 200
    assert info.json()["data"]["username"] == username

    # 缺失/无效 token 均返回 401
    no_token = await client.get("/api/user/info")
    assert no_token.status_code == 401
    bad_token = await client.get("/api/user/info", headers={"Authorization": "bad-token"})
    assert bad_token.status_code == 401


async def test_news_list_and_pagination(client):
    _, auth = await _register_and_login(client)
    for i in range(3):
        await _publish_news(client, auth, f"分页测试新闻{i} {uuid.uuid4().hex[:6]}")

    first_page = await client.get("/api/news/list", params={"categoryId": 8, "page": 1, "pageSize": 2})
    assert first_page.status_code == 200
    data = first_page.json()["data"]
    assert len(data["list"]) == 2
    assert data["total"] >= 3
    assert data["hasMore"] is True

    second_page = await client.get("/api/news/list", params={"categoryId": 8, "page": 2, "pageSize": 2})
    second_ids = {item["id"] for item in second_page.json()["data"]["list"]}
    first_ids = {item["id"] for item in data["list"]}
    assert first_ids.isdisjoint(second_ids)


async def test_publish_invalidates_list_cache(client):
    _, auth = await _register_and_login(client)

    before = await client.get("/api/news/list", params={"categoryId": 7, "page": 1, "pageSize": 10})
    before_total = before.json()["data"]["total"]

    await _publish_news(client, auth, f"缓存失效测试 {uuid.uuid4().hex[:6]}", category_id=7)

    after = await client.get("/api/news/list", params={"categoryId": 7, "page": 1, "pageSize": 10})
    assert after.json()["data"]["total"] == before_total + 1


async def test_favorite_and_history_flow(client):
    _, auth = await _register_and_login(client)
    news_id = await _publish_news(client, auth, f"收藏历史测试 {uuid.uuid4().hex[:6]}")

    added = await client.post("/api/favorite/add", json={"newsId": news_id}, headers=auth)
    assert added.status_code == 200

    check = await client.get("/api/favorite/check", params={"newsId": news_id}, headers=auth)
    assert check.status_code == 200
    assert check.json()["data"]["isFavorite"] is True

    history = await client.post("/api/history/add", json={"newsId": news_id}, headers=auth)
    assert history.status_code == 200
    history_list = await client.get("/api/history/list", headers=auth)
    assert history_list.status_code == 200
    assert any(item["id"] == news_id for item in history_list.json()["data"]["list"])

    # 未登录访问收藏接口 -> 401
    anonymous = await client.get("/api/favorite/list")
    assert anonymous.status_code == 401


async def test_my_news_update_and_delete(client):
    _, auth = await _register_and_login(client)
    news_id = await _publish_news(client, auth, f"增删改测试 {uuid.uuid4().hex[:6]}")

    updated = await client.put(
        f"/api/news/{news_id}",
        data={
            "title": f"增删改测试-改 {uuid.uuid4().hex[:6]}",
            "content": "这是修改后的正文内容，同样超过十个字符。",
            "categoryId": "8",
        },
        headers=auth,
    )
    assert updated.status_code == 200

    deleted = await client.delete(f"/api/news/{news_id}", headers=auth)
    assert deleted.status_code == 200

    mine = await client.get("/api/news/mine", headers=auth)
    assert all(item["id"] != news_id for item in mine.json()["data"]["list"])


async def test_sync_endpoint_requires_token(client):
    wrong_token = await client.post(
        "/api/news/sync", headers={"X-Sync-Token": "wrong-token"}
    )
    assert wrong_token.status_code == 403

    missing_token = await client.post("/api/news/sync")
    assert missing_token.status_code == 403

    status = await client.get("/api/news/sync/status")
    assert status.status_code == 200


async def test_hot_list_and_search(client):
    """全库热榜（按阅读量、数据库聚合）与站内搜索接口。"""
    _, auth = await _register_and_login(client)
    marker = uuid.uuid4().hex[:8]
    news_id = await _publish_news(client, auth, f"热点新闻{marker}事件", category_id=2)

    # 全库热榜
    hot_all = await client.get("/api/news/hot", params={"pageSize": 10})
    assert hot_all.status_code == 200
    assert hot_all.json()["data"]["total"] >= 1

    # 分类热榜包含刚发布的新闻
    hot_category = await client.get("/api/news/hot", params={"categoryId": 2, "pageSize": 10})
    assert news_id in {item["id"] for item in hot_category.json()["data"]["list"]}

    # 搜索命中标题（标题形如 热点新闻{marker}事件）
    found = await client.get("/api/news/search", params={"keyword": f"新闻{marker}"})
    data = found.json()["data"]
    assert data["total"] >= 1
    assert any(item["id"] == news_id for item in data["list"])

    # 无结果与缺少关键词的分支
    none = await client.get("/api/news/search", params={"keyword": "绝不存在的关键词组合xyz"})
    assert none.json()["data"]["total"] == 0
    missing_keyword = await client.get("/api/news/search")
    assert missing_keyword.status_code == 422


async def test_ai_history_persistence(client):
    """登录用户的问答自动保存为历史，匿名不保存；支持查询与删除。"""
    _, auth = await _register_and_login(client)
    marker = uuid.uuid4().hex[:8]

    chat = await client.post(
        "/api/ai/chat",
        json={"messages": [{"role": "user", "content": f"帮我看看{marker}的新闻"}]},
        headers=auth,
    )
    assert chat.status_code == 200

    history = await client.get("/api/ai/history", headers=auth)
    assert history.status_code == 200
    data = history.json()["data"]
    record = next((item for item in data["list"] if marker in item["message"]), None)
    assert record is not None
    assert record["response"].strip()

    # 匿名请求不保存历史
    await client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": f"匿名提问{marker}"}]})
    anonymous_check = await client.get("/api/ai/history", headers=auth)
    assert all(f"匿名提问{marker}" not in item["message"] for item in anonymous_check.json()["data"]["list"])

    # 删除自己的记录
    deleted = await client.delete(f"/api/ai/history/{record['id']}", headers=auth)
    assert deleted.status_code == 200
    after = await client.get("/api/ai/history", headers=auth)
    assert all(item["id"] != record["id"] for item in after.json()["data"]["list"])

    # 未登录访问历史 -> 401
    assert (await client.get("/api/ai/history")).status_code == 401


async def test_ai_chat_db_fallback_and_rate_limit(client):
    """AI 未配置 Key 时：命中站内新闻则返回数据库兜底回答（SSE 格式与上游一致）。"""
    _, auth = await _register_and_login(client)
    marker = uuid.uuid4().hex[:8]
    await _publish_news(client, auth, f"量子计算机突破{marker}重大进展", category_id=8)

    chat = await client.post(
        "/api/ai/chat",
        json={"messages": [{"role": "user", "content": f"量子计算机{marker}最近有什么新闻"}]},
    )
    assert chat.status_code == 200
    body = chat.text
    assert "data:" in body and "[DONE]" in body
    assert "站内新闻库" in body
    assert marker in body

    # 限流：连续超过 AI_CHAT_RATE_LIMIT_PER_HOUR（默认 20）次后返回 429
    # （该用例放在文件最后，避免消耗同 IP 的其他用例配额）
    codes = []
    for _ in range(25):
        response = await client.post(
            "/api/ai/chat",
            json={"messages": [{"role": "user", "content": "随便聊聊"}]},
        )
        codes.append(response.status_code)

    assert codes[0] == 200
    assert 429 in codes
