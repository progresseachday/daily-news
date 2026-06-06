import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

# 讀取環境變數
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 📊 全球權威金融與技術新聞源
RSS_FEEDS = {
    "CNBC Markets": "https://www.cnbc.com/id/10000115/device/rss/rss.html",
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "Reuters Business": "https://services.radio-france.fr/rss/v2/depeches/reuters/business.xml",
    "Nikkei Asia Tech": "https://asia.nikkei.com/rss/feed/nar",
    "TechCrunch": "https://techcrunch.com/feed/",
    "VentureBeat": "https://venturebeat.com/feed/"
}

def clean_html_text(raw_html):
    """移除 RSS 描述中夾雜的 HTML 標籤"""
    if not raw_html:
        return ""
    clean_re = re.compile('<.*?>')
    return re.sub(clean_re, '', raw_html).strip()

def fetch_global_rss_data():
    """爬取全球權威媒體 RSS 事實文本"""
    combined_corpus = []
    print("📡 開始即時同步全球華爾街與 PE 級新聞源Facts...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/53736 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/53736"
    }

    for name, url in RSS_FEEDS.items():
        try:
            print(f"🔄 正在連線權威源: {name}...")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue
                
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            count = 0
            for item in items:
                if count >= 4:
                    break
                title = item.find("title")
                link = item.find("link")
                desc = item.find("description")
                
                title_txt = title.text if title is not None else ""
                link_txt = link.text if link is not None else ""
                desc_txt = clean_html_text(desc.text) if desc is not None else ""
                
                if len(desc_txt) > 150:
                    desc_txt = desc_txt[:150] + "..."
                
                if title_txt and link_txt:
                    combined_corpus.append(f"來源: {name}\n標題: {title_txt}\n網址: {link_txt}\n內文: {desc_txt}\n---")
                    count += 1
            print(f"✅ {name} 同步成功。")
        except Exception as e:
            print(f"❌ 解析 {name} 發生阻礙: {str(e)}")
            
    return "\n\n".join(combined_corpus)

def generate_wall_street_facts_summary(raw_corpus):
    """呼叫 Groq 進行極致去重與高密度硬核數據提煉"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = (
        "你現在是華爾街頂級私募基金（PE）的常務董事兼投資委員會主席。你擁有極其嚴謹的商業分析與數據傳導邏輯。妳蔑視一切缺乏數據支撐的情感描述和空泛詞彙（如「大幅拉高」、「前景看好」、「市場好消息」、「帶來實質衝擊」等皆為不合格的廢話）。\n\n"
        "【⚠️ 投資委員會硬核輸出紀律 —— 違者開除】\n"
        "1. 🚨【不准輸出提示詞範例】禁止將本提示詞中用中括號或引號說明的「格式說明文字」當成文本輸出！你必須直接讀取當天實際抓取到的 RSS 文本 facts，若 RSS 文本中缺乏具體數字，請用正統金融邏輯推導具體影響，絕不准出現任何代稱符號！\n"
        "2. 🚨【全繁體中文】所有輸出的文字（包含事件名稱、事實摘要、金融判讀）一律必須使用【繁體中文（台灣習慣用語）】！\n"
        "3. 🚨【強數據導向】「新聞Facts」中必須強制引用原文中的具體硬數據（如：百分比 %、貨幣金額 $、基點 bps、產量、估值、融資額）。如果原始 RSS 內文確實沒有數字，則必須在後方的【投行判讀】中，給出量化的邏輯鏈，嚴禁只講好壞感覺。\n"
        "4. ❌ 嚴禁輸出任何 Markdown 語法（例如 **, *, #）。請直接輸出符合標準、能在 Gmail 中完美渲染的 HTML 標籤。總條目數保持在 6~9 條。\n\n"
        "【三大維度 HTML 高效輸出格式】（請嚴格依據當天實際新聞填入，不准照抄以下說明文字）：\n\n"
        "<h3>📊 總體經濟、流動性與跨境匯率（資本成本視角）</h3>\n"
        "● <b>[請在此填入當天實際巨集事件簡稱，勿超過15字]</b>：[提煉當天新聞事實，必須包含具體數據或政策方向] <span style='color: #0f766e; font-weight: 500;'>➔【投行金融判讀】[拒絕空話！請精準指出此數字如何透過貨幣傳導機制，實質拉升或降低企業的加權平均資本成本（WACC），並說明對資本市場流動性的具體傳導方向。]</span> <a href='[請填入當天實際網址]' style='color: #007bff; text-decoration: none; font-weight: bold;'>🔗 原文連結</a>\n\n"
        "<h3>🌍 地緣政治、跨境供應鏈與能源基礎設施（營運韌性視角）</h3>\n"
        "● <b>[請在此填入當天實際供應鏈事件簡稱，勿超過15字]</b>：[提煉當天航運、關稅、半導體或能源硬事實與關鍵數字] <span style='color: #0f766e; font-weight: 500;'>➔【投行金融判讀】[拒絕空話！請精準分析該數據或事件如何引發斷鏈，並如何實質衝擊跨境企業的投入資本回報率（ROIC）或擠壓其供應鏈毛利防線。]</span> <a href='[請填入當天實際網址]' style='color: #007bff; text-decoration: none; font-weight: bold;'>🔗 原文連結</a>\n\n"
        "<h3>💡 AI 前沿突破、新創資本配置與監管防線（商業化視角）</h3>\n"
        "● <b>[請在此填入當天實際技術或募資項目簡稱，勿超過15字]</b>：[提煉當天新創融資金額、估值、或 AI 核心基準測試之事實數字] <span style='color: #0f766e; font-weight: 500;'>➔【投行金融判讀】[拒絕空話！請從商業競爭與財務結構出發，一針見血地判斷該項目的營運槓桿（Operating Leverage）或是否具備真正的產業經濟護城河（Moat）。]</span> <a href='[請填入當天實際網址]' style='color: #007bff; text-decoration: none; font-weight: bold;'>🔗 原文連結</a>\n\n"
        f"--- 今日實際抓取之 RSS 原始數據文本 ---\n{raw_corpus}"
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,  # 降低隨機性，讓 AI 極度嚴謹
        "max_tokens": 4000
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Groq API 報錯: {response.text}")

def send_pure_html_email(html_content_body):
    """將高效、高數據密度的情報發送至信箱"""
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER
    
    current_date_str = datetime.now().strftime("%Y年%m月%d日")
    msg["Subject"] = f"【頂級決策智庫】{current_date_str} 全球資本與技術連動情報"
    
    final_html = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #111; max-width: 850px; margin: 0 auto; padding: 15px;">
        <div style="margin-bottom: 25px;">
            {html_content_body}
        </div>
        <hr style="border: 0; border-top: 1px solid #ddd; margin-top: 30px;">
        <p style="font-size: 11px; color: #777; margin-top: 10px;">數據矩陣：CNBC / MarketWatch / Reuters / Nikkei Asia / TechCrunch</p>
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
        if not rss_corpus.strip():
            print("⚠️ 未能在全球 RSS 源中捕獲到任何有效數據。")
        else:
            final_report = generate_wall_street_facts_summary(rss_corpus)
            send_pure_html_email(final_report)
            print("🎉 任務完美達成，高密度數據信件已成功發送！")
    except Exception as e:
        print(f"❌ 執行中斷錯誤: {str(e)}")
        exit(1)
