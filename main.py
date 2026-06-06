import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

# 讀取環境變數（從保險箱拿鑰匙）
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 📊 權威 RSS 新聞源（客製化只需從這裡修改網址）
RSS_FEEDS = {
    "CNBC Markets": "https://www.cnbc.com/id/10000115/device/rss/rss.html",
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "Reuters Business": "https://services.radio-france.fr/rss/v2/depeches/reuters/business.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "VentureBeat": "https://venturebeat.com/feed/"
}

def clean_html_text(raw_html):
    if not raw_html: return ""
    return re.sub(re.compile('<.*?>'), '', raw_html).strip()

def fetch_global_rss_data():
    combined_corpus = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for name, url in RSS_FEEDS.items():
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200: continue
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            count = 0
            for item in items:
                if count >= 4: break
                title = item.find("title")
                link = item.find("link")
                desc = item.find("description")
                
                title_txt = title.text if title is not None else ""
                link_txt = link.text if link is not None else ""
                desc_txt = clean_html_text(desc.text) if desc is not None else ""
                if len(desc_txt) > 150: desc_txt = desc_txt[:150] + "..."
                
                if title_txt and link_txt:
                    combined_corpus.append(f"來源: {name}\n標題: {title_txt}\n網址: {link_txt}\n大意: {desc_txt}\n---")
                    count += 1
        except Exception as e:
            print(f"❌ 無法讀取 {name}: {str(e)}")
            
    return "\n\n".join(combined_corpus)

def generate_wall_street_facts_summary(raw_corpus):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    prompt = (
        "# Role\n"
        "你現在是華爾街頂級私募基金的投資委員會主席。你擁有極其嚴謹的金融大局觀。\n\n"
        "# Task\n"
        "請審視今日所有 RSS 新聞文本，挖掘出核心數字，並套用正統經濟學邏輯進行深度判讀。\n\n"
        "【⚠️ 至高赤字禁令 —— 違者開除】\n"
        "1. 🚨【語言命令】所有輸出的文字（包含事件名稱、新聞事實大意、投行判讀）一律必須使用【繁體中文（台灣習慣用語）】！絕對不准留下一句英文原始文本！必須由你將英文完全翻譯並精煉成台灣人能秒讀的繁體中文！\n"
        "2. ❌ 嚴禁輸出任何 Markdown 語法（不要出現 **, *, # ）。請直接輸出符合標準、能在 Gmail 中完美渲染的 HTML 標籤。\n"
        "3. 信件開頭與結尾不要有任何客套話，直接從第一個 <h3> 標籤開始輸出。\n\n"
        "【三大決策維度與 HTML 雙色格式化輸出規定】\n"
        "<h3>📊 總體經濟與跨境匯率（資本成本視角）</h3>\n"
        "<p style='margin: 12px 0; font-size: 14px; line-height: 1.6;'>● <b>[繁體中文事件名稱]</b>：[將當天新聞 facts 完全翻譯成中文大意] <span style='color: #0f766e; font-weight: 500;'>➔【投行判讀】[用投資學理論判斷此數據對市場的利基]</span> <a href='對應網址' style='color: #007bff; text-decoration: none;'>🔗 原文連結</a></p>\n\n"
        "<h3>🌍 地緣政治與跨境供應鏈（營運韌性視角）</h3>\n"
        "<p style='margin: 12px 0; font-size: 14px; line-height: 1.6;'>● <b>[繁體中文事件名稱]</b>：[中文 facts 大意] <span style='color: #0f766e; font-weight: 500;'>➔【投行判讀】[產業衝擊分析]</span> <a href='對應網址' style='color: #007bff; text-decoration: none;'>🔗 原文連結</a></p>\n\n"
        "<h3>💡 AI 前沿突破與新創資本（商業化視角）</h3>\n"
        "<p style='margin: 12px 0; font-size: 14px; line-height: 1.6;'>● <b>[繁體中文項目名稱]</b>：[中文 facts 大意] <span style='color: #0f766e; font-weight: 500;'>➔【投行判讀】[商業競爭護城河分析]</span> <a href='對應網址' style='color: #007bff; text-decoration: none;'>🔗 原文連結</a></p>\n\n"
        f"--- 當天原始 RSS 數據文本 ---\n{raw_corpus}"
    )
    
payload = {
        "model": "llama-3.3-70b-specdec",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.15,
        "max_tokens": 4000
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Groq API 報錯: {response.text}")

def send_pure_html_email(html_content_body):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER
    msg["Subject"] = f"【頂級決策智庫】{datetime.now().strftime('%Y年%m月%d日')} 全球資本連動情報"
    
    final_html = f"""
    <html>
    <body style="font-family: sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 10px;">
        <div>{html_content_body}</div>
    </body>
    </html>
    """
    msg.attach(MIMEText(final_html, "html", "utf-8"))
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
    server.quit()

if __name__ == "__main__":
    try:
        rss_corpus = fetch_global_rss_data()
        if rss_corpus.strip():
            final_report = generate_wall_street_facts_summary(rss_corpus)
            send_pure_html_email(final_report)
            print("🎉 成功發送日報！")
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        exit(1)

