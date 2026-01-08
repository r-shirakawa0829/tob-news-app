import streamlit as st
import feedparser
import pandas as pd
import datetime
import os
import urllib.parse

# --- 判定ロジック：成長意欲・toB判定 ---
def analyze_growth_company(title, summary):
    text = (title + summary).lower()
    growth_keywords = ["採用", "募集", "移転", "増床", "新拠点", "海外展開", "新規事業", "資金調達", "提携", "導入", "開始", "ローンチ", "子会社", "拠点を新設"]
    biz_keywords = ["法人", "企業", "b2b", "saas", "dx", "ソリューション", "oem", "卸", "加盟", "fc", "コンサル", "プラットフォーム"]
    return any(k in text for k in growth_keywords) and any(k in text for k in biz_keywords)

def fetch_all_sources():
    feeds = [
        "https://prtimes.jp/index.rdf",
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("採用強化 企業") + "&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("新拠点 設立") + "&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("新規事業 開始") + "&hl=ja&gl=JP&ceid=JP:ja"
    ]
    
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    new_entries = []
    
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if analyze_growth_company(entry.title, entry.summary):
                # 社名の簡易抽出
                title_clean = entry.title.replace("【", " ").replace("】", " ").replace("「", " ").replace("」", " ")
                company = title_clean.split("が")[0].split("の")[0].strip()[:20]
                
                pub_date = today_str
                if hasattr(entry, 'published'):
                    try: pub_date = pd.to_datetime(entry.published).strftime("%Y-%m-%d")
                    except: pass
                
                new_entries.append([pub_date, time_str, company, entry.title, entry.link])
    
    db_file = "news_database.csv"
    if new_entries:
        df_new = pd.DataFrame(new_entries, columns=["date", "time", "company", "title", "url"])
        if os.path.exists(db_file):
            try:
                df_old = pd.read_csv(db_file)
                # 列が足りない古いデータの場合は捨てる
                if "company" not in df_old.columns:
                    df_final = df_new
                else:
                    df_final = pd.concat([df_new, df_old]).drop_duplicates(subset=["url"], keep="first")
            except:
                df_final = df_new
        else:
            df_final = df_new
        
        df_final = df_final.sort_values(by=["date", "time"], ascending=False)
        df_final.to_csv(db_file, index=False, encoding="utf_8_sig")
        return len(new_entries)
    return 0

# --- 画面デザイン ---
st.set_page_config(page_title="Growth Company Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stCard { border: 1px solid #dee2e6; padding: 20px; border-radius: 12px; background: white; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .new-label { background: linear-gradient(45deg, #ff4b4b, #ff8f8f); color: white; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; margin-right: 10px; }
    .tag { background-color: #e9ecef; color: #495057; padding: 3px 10px; border-radius: 5px; font-size: 11px; margin-right: 5px; border: 1px solid #ced4da; }
    .company-name { color: #6c757d; font-size: 13px; font-weight: 600; margin-bottom: 5px; }
    .title-link { color: #1f77b4; font-size: 18px; font-weight: bold; text-decoration: none; }
    .title-link:hover { text-decoration: underline; color: #125688; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 成長企業ターゲット・リスト")
st.caption("最新順に並んでいます。初めて検出された企業には NEW ラベルが表示されます。")

db_file = "news_database.csv"

if st.button("🔄 最新情報をスキャンして更新"):
    with st.spinner("情報を集めています..."):
        count = fetch_all_sources()
        st.success(f"{count} 件の新しいニュースを反映しました。")
        st.rerun()

st.divider()

if os.path.exists(db_file):
    df = pd.read_csv(db_file)
    if not df.empty:
        # 日付リストを降順で
        dates = df["date"].unique()
        
        for d in dates:
            st.markdown(f"#### 📅 {d}")
            day_df = df[df["date"] == d]
            
            for _, row in day_df.iterrows():
                # NEW判定：過去の日付（自身より古い日付）にその社名があるか
                past_data = df[df["date"] < row['date']]
                is_new = row['company'] not in past_data['company'].values if not past_data.empty else True
                
                # タグ
                tags = []
                if "採用" in str(row['title']): tags.append("🔥 採用強化")
                if "資金" in str(row['title']): tags.append("💰 資金調達")
                if "拠点" in str(row['title']) or "移転" in str(row['title']): tags.append("📍 拠点拡大")
                if "事業" in str(row['title']) or "開始" in str(row['title']): tags.append("🚀 新事業")
                
                new_badge = '<span class="new-label">NEW</span>' if is_new else ""
                tag_html = "".join([f'<span class="tag">{t}</span>' for t in tags])
                
                st.markdown(f"""
                <div class="stCard">
                    <div class="company-name">{row['time']} | {row['company']}</div>
                    {new_badge}<a class="title-link" href="{row['url']}" target="_blank">{row['title']}</a>
                    <div style="margin-top: 10px;">{tag_html}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("データが空です。更新ボタンを押してください。")
else:
    st.info("「最新情報をスキャンして更新」ボタンを押すとリストが作成されます。")
