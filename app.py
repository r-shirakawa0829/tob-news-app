import streamlit as st
import feedparser
import pandas as pd
import datetime
import os

# --- 判定ロジック（前回の強化版を維持） ---
def is_tob_news(title, summary):
    text = (title + summary).lower()
    biz_keywords = ["fc", "フランチャイズ", "加盟店", "卸", "業務用", "法人向け", "oem", "dx", "saas", "店舗開発", "福利厚生", "オフィス用"]
    if any(k in text for k in biz_keywords): return True
    consumer_keywords = ["新発売", "期間限定", "食べ放題", "実食レポ", "公式sns"]
    if any(k in title for k in consumer_keywords): return False
    base_tob = ["提携", "導入", "開始", "支援", "ソリューション", "開発", "調達", "設立"]
    return any(k in text for k in base_tob)

def fetch_news():
    urls = [
        "https://prtimes.jp/main/html/searchrlp/ctcd/100/f/rss.xml", # スタートアップ
        "https://prtimes.jp/main/html/searchrlp/ctcd/13/f/rss.xml"   # 外食・中堅
    ]
    today = datetime.date.today().strftime("%Y-%m-%d")
    new_data = []
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if is_tob_news(entry.title, entry.summary):
                new_data.append([today, entry.title, entry.link])
    
    db_file = "news_database.csv"
    df_new = pd.DataFrame(new_data, columns=["date", "title", "url"])
    if os.path.exists(db_file):
        df_old = pd.read_csv(db_file)
        df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=["url"])
    else:
        df_final = df_new
    df_final.to_csv(db_file, index=False, encoding="utf_8_sig")
    return df_final

# --- 画面表示 (Streamlit) ---
st.set_page_config(page_title="toB企業ニュースカレンダー", layout="wide")
st.title("📅 toB企業ニュース・カレンダー")

db_file = "news_database.csv"

# サイドバー：手動追加・取得機能
st.sidebar.header("機能メニュー")
if st.sidebar.button("最新ニュースを自動取得"):
    fetch_news()
    st.success("取得しました！")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("➕ ニュースを手動追加")
new_date = st.sidebar.date_input("追加する日付", datetime.date.today())
new_title = st.sidebar.text_input("ニュースのタイトル")
new_url = st.sidebar.text_input("URL (任意)")

if st.sidebar.button("カレンダーに追加"):
    if new_title:
        add_data = pd.DataFrame([[new_date.strftime("%Y-%m-%d"), new_title, new_url]], columns=["date", "title", "url"])
        if os.path.exists(db_file):
            df_old = pd.read_csv(db_file)
            df_final = pd.concat([df_old, add_data]).drop_duplicates()
        else:
            df_final = add_data
        df_final.to_csv(db_file, index=False, encoding="utf_8_sig")
        st.sidebar.success("追加しました！")
        st.rerun()
    else:
        st.sidebar.error("タイトルを入力してください")

# メインエリア：カレンダーウィジェット
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("日付を選択")
    # 視覚的なカレンダーを表示
    selected_date = st.date_input("ニュースを見たい日をクリックしてください", datetime.date.today())
    target_date_str = selected_date.strftime("%Y-%m-%d")

with col2:
    st.subheader(f"🔍 {target_date_str} のニュース")
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        # 文字列として比較するために変換
        display_df = df[df["date"] == target_date_str]
        
        if len(display_df) == 0:
            st.info("この日のニュースはありません。")
        else:
            for _, row in display_df.iterrows():
                link = row['url'] if pd.notna(row['url']) and row['url'] != "" else "#"
                st.markdown(f"✅ [{row['title']}]({link})")
    else:
        st.warning("データがありません。サイドバーから取得してください。")
