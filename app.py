import streamlit as st
import feedparser
import pandas as pd
import datetime
import os
import urllib.parse

# --- 判定ロジック ---
def analyze_growth_company(title, summary):
    text = (title + summary).lower()
    growth_keywords = ["採用", "募集", "移転", "増床", "新拠点", "海外展開", "新規事業", "資金調達", "提携", "導入", "開始", "ローンチ", "子会社"]
    biz_keywords = ["法人", "企業", "b2b", "saas", "dx", "ソリューション", "oem", "卸", "加盟", "fc", "コンサル"]
    return any(k in text for k in growth_keywords) and any(k in text for k in biz_keywords)

def fetch_all_sources():
    feeds = [
        "https://prtimes.jp/index.rdf",
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("採用強化 企業") + "&hl=ja&gl=JP&ceid=JP:ja",
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
                pub_date = today_str
                if hasattr(entry, 'published'):
                    try: pub_date = pd.to_datetime(entry.published).strftime("%Y-%m-%d")
                    except: pass
                
                # 簡易的にタイトルから社名を推測（「株式会社〇〇が〜」の形式が多い想定）
                company = entry.title.split("」")[0].split("】")[0].split("が")[0].strip()
                new_entries.append([pub_date, time_str, company, entry.title, entry.link])
    
    db_file = "news_database.csv"
    if new_entries:
        df_new = pd.DataFrame(new_entries, columns=["date", "time", "company", "title", "url"])
        if os.path.exists(db_file):
            df_old = pd.read_csv(db_file)
            # 既存リストにない会社名を「新規」としてマークするための準備
            existing_companies = set(df_old["company"].unique())
            df_final = pd.concat([df_new, df_old]).drop_duplicates(subset=["url"], keep="first")
        else:
            existing_companies = set()
            df_final = df_new
        
        df_final = df_final.sort_values(by=["date", "time"], ascending=False)
        df_final.to_csv(db_file, index=False, encoding="utf_8_sig")
        return len(new_entries), existing_companies
    return 0, set()

# --- Streamlit デザイン設定 ---
st.set_page_config(page_title="Growth Company Hub", layout="wide")

# カスタムCSSで見た目を整える
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stCard { border: 1px solid #e6e9ef; padding: 15px; border-radius: 10px; background: white; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .new-label { background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 8px; }
    .tag { background-color: #007bff; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 成長企業ニュース・タイムライン")
st.caption("PR TIMES・Googleニュースから成長意欲の高いtoB企業を自動抽出しています")

db_file = "news_database.csv"

# 更新ボタン
if st.button("🔄 最新情報を取得して更新"):
    with st.spinner("スキャニング中..."):
        count, _ = fetch_all_sources()
        st.success(f"{count}件の記事を確認しました。")
        st.rerun()

st.divider()

if os.path.exists(db_file):
    df = pd.read_csv(db_file)
    
    # 過去の会社リストを取得（NEWラベル判定用）
    # 現在表示されているデータの中で、それ以前のデータに名前がないものを判定
    dates = df["date"].unique()
    
    for d in dates:
        st.markdown(f"### 📅 {d}")
        day_df = df[df["date"] == d]
        
        for idx, row in day_df.iterrows():
            # NEWラベル判定：この会社がこれ以前（古い日付）のデータに存在するか
            past_data = df[df["date"] < d]
            is_new = row['company'] not in past_data['company'].values if not past_data.empty else True
            
            # タグ生成
            tags = []
            if "採用" in str(row['title']): tags.append("🔥採用強化")
            if "資金" in str(row['title']): tags.append("💰資金調達")
            if "移転" in str(row['title']) or "拠点" in str(row['title']): tags.append("📍拠点拡大")
            if "新サービス" in str(row['title']) or "開始" in str(row['title']): tags.append("🚀新事業")

            # HTMLでカード風の見た目を作成
            new_badge = '<span class="new-label">NEW</span>' if is_new else ""
            tag_html = "".join([f'<span class="tag">{t}</span>' for t in tags])
            
            with st.container():
                st.markdown(f"""
                <div class="stCard">
                    <small>{row['time']} | {row['company']}</small>< pybr>
                    {new_badge}<strong><a href="{row['url']}" target="_blank" style="text-decoration: none; color: #1f77b4;">{row['title']}</a></strong><br>
                    <div style="margin-top: 8px;">{tag_html}</div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("「最新情報を取得」ボタンを押してスキャンを開始してください。")
