import streamlit as st
import feedparser
import pandas as pd
import datetime
import os

# 設定：toB向けのキーワード
INCLUDE_KEYWORDS = ["法人向け", "BtoB", "SaaS", "DX", "業務効率化", "ソリューション", "提携", "調達"]
EXCLUDE_KEYWORDS = ["人事", "スイーツ", "カフェ", "アパレル", "発売記念"]

def fetch_news():
    url = "https://prtimes.jp/main/html/searchrlp/ctcd/100/f/rss.xml"
    feed = feedparser.parse(url)
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    data = []
    for entry in feed.entries:
        is_tob = any(k in entry.title + entry.summary for k in INCLUDE_KEYWORDS)
        is_major = any(k in entry.title for k in EXCLUDE_KEYWORDS)
        if is_tob and not is_major:
            data.append([today, entry.title, entry.link])
    
    db_file = "news_database.csv"
    df_new = pd.DataFrame(data, columns=["date", "title", "url"])
    if os.path.exists(db_file):
        df_old = pd.read_csv(db_file)
        df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=["url"])
    else:
        df_final = df_new
    df_final.to_csv(db_file, index=False, encoding="utf_8_sig")

# --- Streamlit 表示設定 ---
st.title("🏢 toB企業ニュース一覧")
if os.path.exists("news_database.csv"):
    df = pd.read_csv("news_database.csv")
    date_list = sorted(df["date"].unique(), reverse=True)
    selected_date = st.sidebar.selectbox("日付を選択", date_list)
    st.subheader(f"📅 {selected_date} のニュース")
    for _, row in df[df["date"] == selected_date].iterrows():
        st.markdown(f"・ [{row['title']}]({row['url']})")
