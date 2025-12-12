import feedparser
import requests
import json
import os
import datetime
import pytz
from openai import OpenAI

# --- 配置区域 (从环境变量获取，安全第一) ---
# 建议在GitHub Secrets中配置这些 Key
API_KEY = os.getenv("LLM_API_KEY")
API_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com") # 默认为DeepSeek
MODEL_NAME = os.getenv("LLM_MODEL", "deepseek-chat")
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")

# 定义高质量AI新闻源 (RSS)
RSS_FEEDS = [
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Hacker News (AI)", "url": "https://hnrss.org/newest?q=AI"},
    # 你可以在这里继续添加
]

def get_recent_news():
    """获取过去24小时的新闻标题和链接"""
    print("正在抓取新闻...")
    news_content = ""
    #以此刻为基准，推算24小时前的时间
    now = datetime.datetime.now(datetime.timezone.utc)
    one_day_ago = now - datetime.timedelta(hours=24)

    for feed in RSS_FEEDS:
        try:
            d = feedparser.parse(feed["url"])
            print(f"正在解析: {feed['name']}")
            count = 0
            for entry in d.entries:
                # 尝试解析发布时间
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
                
                # 如果找不到时间，默认取前3条；如果找到时间，只取24h内的
                if (published_time and published_time > one_day_ago) or (not published_time and count < 3):
                    news_content += f"- [{feed['name']}] {entry.title}: {entry.link}\n"
                    count += 1
        except Exception as e:
            print(f"解析 {feed['name']} 失败: {e}")
    
    return news_content

def summarize_with_ai(content):
    """调用大模型进行总结"""
    if not content:
        return "过去24小时没有检测到重要更新。"
    
    print("正在进行AI总结...")
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    prompt = f"""
    你是专业的AI行业分析师。请根据以下抓取到的新闻列表，写一份“每日AI早报”。
    
    要求：
    1. 筛选出最有价值的3-5条新闻。
    2. 格式：
       **标题** (emoji)
       > 一句话深度解读，说明它为什么重要。
    3. 最后给出一个“行业风向”的一句话点评。
    4. 必须使用中文。

    新闻列表：
    {content}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
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
    # 1. 获取
    raw_news = get_recent_news()
    # 2. 总结
    summary = summarize_with_ai(raw_news)
    # 3. 推送
    if PUSHPLUS_TOKEN:
        send_pushplus(summary)
    else:
        print("未配置推送Token，直接打印结果：")
        print(summary)