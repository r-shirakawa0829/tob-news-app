import streamlit as st
import feedparser
import pandas as pd
import datetime
import os
import urllib.parse

# --- 判定ロジック：成長意欲のあるtoB企業を抽出 ---
def analyze_growth_company(title, summary):
    text = (title + summary).lower()
    # 成長意欲を示すワード
    growth_keywords = ["採用", "募集", "移転", "増床", "新拠点", "海外展開", "新規事業", "資金調達", "提携", "導入", "開始", "ローンチ"]
    # ビジネスワード
    biz_keywords = ["法人", "企業", "b2b", "saas", "dx", "ソリューション", "oem", "卸", "加盟", "fc"]

    is_growth = any(k in text for k in growth_keywords)
    is_biz = any(k in text for k in biz_keywords)
    return is_growth and is_biz

def fetch_all_sources():
    feeds = [
        "https://prtimes.jp/index.rdf", # PR TIMES 総合
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("採用強化 企業") + "&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("新規事業 開始") + "&hl=ja&gl=JP&ceid=JP:ja"
    ]
    
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M") # 取得時刻も記録
    new_data = []
    
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if analyze_growth_company(entry.title, entry.summary):
                pub_date = today_str
                if hasattr(entry, 'published'):
                    try:
                        pub_date = pd.to_datetime(entry.published).strftime("%Y-%m-%d")
                    except: pass
                
                # [日付, 時刻, タイトル, URL] の形式で格納
                new_data.append([pub_date, time_str, entry.title, entry.link])
    
    db_file = "news_database.csv"
    if new_data:
        df_new = pd.DataFrame(new_data, columns=["date", "time", "title", "url"])
        if os.path.exists(db_file):
            df_old = pd.read_csv(db_file)
            # 新しいデータを「上」にして結合し、重複を排除
            df_final = pd.concat([df_new, df_old]).drop_duplicates(subset=["url"], keep="first")
        else:
            df_final = df_new
        
        # 日付と時刻で最新順に並び替え
        df_final = df_final.sort_values(by=["date", "time"], ascending=False)
        df_final.to_csv(db_file, index=False, encoding="utf_8_sig")
        return len(new_data)
    return 0

# --- Streamlit UI ---
st.set_page_config(page_title="成長企業キャッチャー", layout="wide")
st.title("🚀 最新：成長意欲のある企業ニュース")

db_file = "news_database.csv"

# 自動更新ボタン
if st.button("🔄 最新情報をスキャンして一番上に追加"):
    with st.spinner("スキャン中..."):
        count = fetch_all_sources()
        st.success(f"{count}件の新しい動きを検知しました。")
        st.rerun()

st.markdown("---")

if os.path.exists(db_file):
    df = pd.read_csv(db_file)
    
    # 日付ごとにグループ化して表示
    dates = df["date"].unique()
    
    for d in dates:
        st.subheader(f"📅 {d}")
        day_df = df[df["date"] == d]
        
        for _, row in day_df.iterrows():
            # ラベル付け
            tags = ""
            if "採用" in str(row['title']): tags += " 🔥採用"
            if "資金" in str(row['title']): tags += " 💰調達"
            if "移転" in str(row['title']) or "拠点" in str(row['title']): tags += " 📍拡大"
            
            # 取得時刻を表示することで「積み上がっている感」を出す
            time_prefix = f"[{row['time']}] " if 'time' in df.columns else ""
            st.markdown(f"{time_prefix}**{tags}** [{row['title']}]({row['url']})")
else:
    st.info("データがありません。「最新情報をスキャン」ボタンを押してください。")
