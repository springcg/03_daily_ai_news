## AI 早报自动推送脚本

每日定时抓取多家 AI 新闻源（RSS），汇总近 24 小时的要闻，调用 OpenAI 兼容接口生成中文早报，并通过 PushPlus 推送到微信。

### 功能
- 抓取新闻源：`机器之心`、`OpenAI Blog`、`Hacker News (AI)`（可自行添加）。
- 过滤近 24 小时内的更新，或在无时间戳时取前 3 条。
- 调用 `OpenAI` 客户端（支持通过 `base_url` 指向 DeepSeek 等兼容服务）生成摘要。
- 使用 PushPlus 以 Markdown 格式推送。

### 本地运行
1) 安装依赖  
`pip install -r requirements.txt`

2) 配置环境变量（示例）  
```bash
export LLM_API_KEY="你的API密钥"
export LLM_BASE_URL="https://api.deepseek.com"   # 可改为任何兼容 OpenAI 协议的地址
export LLM_MODEL="deepseek-chat"                  # 具体模型名按服务端配置
export PUSHPLUS_TOKEN="你的PushPlus Token"
```

3) 运行脚本  
`python main.py`

未配置 `PUSHPLUS_TOKEN` 时，程序会直接在控制台输出生成的早报。

### GitHub Actions 定时任务
仓库内的工作流 `.github/workflows/daily.yml` 会在每天 UTC 23:00（北京时间 07:00）触发，并可手动 `workflow_dispatch`。请在仓库 Secrets 配置：
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `PUSHPLUS_TOKEN`

### 自定义新闻源
在 `main.py` 中修改 `RSS_FEEDS` 列表，添加形如：
```python
{"name": "Your Source", "url": "https://example.com/rss"}
```

### 目录说明
- `main.py`：核心逻辑（抓取、总结、推送）。
- `requirements.txt`：Python 依赖。
- `.github/workflows/daily.yml`：定时/手动触发工作流。

