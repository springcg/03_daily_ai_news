import feedparser
import requests
import json
import os
import datetime
import pytz
from openai import OpenAI

# --- 配置区域 ---
API_KEY = os.getenv("LLM_API_KEY")
API_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = os.getenv("LLM_MODEL", "deepseek-chat")
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")

# 【修改处 1】优化了信息源，涵盖新闻、官方博客、技术社区
RSS_FEEDS = [
    # --- 综合新闻 ---
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
    {"name": "Hacker News (AI)", "url": "https://hnrss.org/newest?q=AI"},
    # --- 官方技术博客 (最硬核的一手信息) ---
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/"},
]

def get_recent_news():
    """获取过去24小时的新闻，包含标题、链接和摘要"""
    print("正在抓取新闻...")
    news_content = ""
    now = datetime.datetime.now(datetime.timezone.utc)
    one_day_ago = now - datetime.timedelta(hours=24)

    for feed in RSS_FEEDS:
        try:
            d = feedparser.parse(feed["url"])
            print(f"正在解析: {feed['name']}")
            count = 0
            for entry in d.entries:
                published_time = None
                # 尝试解析发布时间
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
                
                # 时间过滤逻辑：有时间则判断24h内，无时间则默认取前3条
                if (published_time and published_time > one_day_ago) or (not published_time and count < 3):
                    # 【修改处 2-A】获取摘要，不仅仅是标题
                    # 优先取 summary, 如果没有则取 description，再没有就空
                    raw_summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
                    # 简单清洗：截取前300字，去除换行符，防止token消耗过多
                    clean_summary = raw_summary[:300].replace('\n', ' ')
                    
                    # 【修改处 2-B】使用 XML 标签包裹，帮助 AI 区分每条新闻的边界
                    news_content += f"""
<item>
    <source>{feed['name']}</source>
    <title>{entry.title}</title>
    <link>{entry.link}</link>
    <summary>{clean_summary}</summary>
</item>
"""
                    count += 1
        except Exception as e:
            print(f"解析 {feed['name']} 失败: {e}")

    return news_content

def summarize_with_ai(content):
    """调用大模型进行筛选和总结"""
    if not content.strip():
        return "过去24小时没有检测到重要更新。"

    print("正在进行AI筛选与总结...")
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    # 【修改处 3】使用更高级的 Prompt，植入筛选标准
    prompt = f"""
    你是 DeepSeek 驱动的首席AI科技编辑。请从以下 RSS 数据中筛选出最重要的 10-20 条信息，生成一份“每日AI早报”。

    【筛选标准 - 请基于以下维度评估，不重要的直接丢弃】：
    1. **技术突破**：SOTA模型发布、架构创新、性能大幅提升。
    2. **开源生态**：知名项目（如Llama, LangChain）的重大更新。
    3. **行业风向**：OpenAI/Google等巨头的战略动作。
    4. **过滤垃圾**：忽略纯营销软文、微小的Bug修复。

    【输入数据】：
    {content}

    【输出格式要求 (Markdown)】：
    ## 📅 每日AI精选 ({datetime.date.today()})

    ### 1. [新闻标题](按照新闻重要性降序排序)
    - **来源**: [来源名称]
    - **类型**: [技术突破/开源/行业动态]
    - **深度解读**: [用中文简述核心内容，并一句话说明它为什么重要，不要只翻译摘要]
    - [🔗 原文链接](URL)

    (依次列出10-20条...)

    ---
    **🌪 行业风向标**：
    [一句话总结今天的整体技术或市场趋势]
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, # 降低随机性，让筛选更严谨
        max_tokens=1500
    )
    return response.choices[0].message.content

def send_pushplus(content):
    """推送到微信 (PushPlus)"""
    print("正在推送消息...")
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": f"📅 AI早报 {datetime.date.today()}",
        "content": content,
        "template": "markdown"
    }
    requests.post(url, json=data)

if __name__ == "__main__":
    # 1. 获取 (含摘要)
    raw_news = get_recent_news()
    
    # 打印原始长度供调试
    print(f"抓取原始内容长度: {len(raw_news)} 字符")
    
    # 2. 总结 (含筛选逻辑)
    summary = summarize_with_ai(raw_news)
    
    # 3. 推送
    if PUSHPLUS_TOKEN:
        send_pushplus(summary)
    else:
        print("未配置推送Token，直接打印结果：")
        print("--------------------------------------------------")
        print(summary)
        print("--------------------------------------------------")
