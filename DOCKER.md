# Docker 使用说明

## 本地启动后端

```powershell
cd C:\Users\yzb\Desktop\小程序\今日头条
docker compose up -d --build
```

## 查看日志

```powershell
docker compose logs -f backend
```

## 手动同步新闻

```powershell
curl -X POST http://127.0.0.1:8000/api/news/sync
```

## 停止容器

```powershell
docker compose down
```

## 上传后端镜像

先登录你的镜像仓库：

```powershell
docker login
```

然后执行项目里的推送脚本：

```powershell
cd C:\Users\yzb\Desktop\小程序\今日头条
.\push-backend-image.ps1 -ImageRepo your-registry/toutiao-backend -Tag v1.0.0 -AlsoLatest
```

示例：

```powershell
.\push-backend-image.ps1 -ImageRepo registry.cn-hangzhou.aliyuncs.com/your-namespace/toutiao-backend -Tag v1.0.0 -AlsoLatest
```

脚本会自动执行：

1. 使用 `fastApiProject/Dockerfile` 构建后端镜像
2. 推送 `your-registry/toutiao-backend:v1.0.0`
3. 如果带了 `-AlsoLatest`，再额外推送 `your-registry/toutiao-backend:latest`

## 说明

- `fastApiProject/.env` 和 `news_app.db` 已排除出镜像构建上下文，不会被打进镜像。
- 运行时数据库文件 `news_app.db` 和上传目录 `uploads` 仍通过 `docker-compose.yml` 挂载到容器中。
- 如果 `WORLD_NEWS_API_KEY` 不可用，系统会自动回退到 RSS 抓取逻辑。
