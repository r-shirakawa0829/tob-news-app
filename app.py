import streamlit as st
import feedparser
import pandas as pd
import datetime
import os

# --- 判定ロジックの強化 ---
def is_tob_news(title, summary):
    text = (title + summary).lower()
    
    # 強制toBワード：これがあればスイーツだろうが何だろうが残す
    biz_keywords = ["fc", "フランチャイズ", "加盟店", "卸", "業務用", "法人向け", "oem", "dx", "saas", "店舗開発", "福利厚生", "オフィス用"]
    if any(k in text for k in biz_keywords):
        return True
    
    # toC除外ワード：ビジネスワードがない状態でこれらがあれば除外
    consumer_keywords = ["新発売", "期間限定", "食べ放題", "実食レポ", "公式sns"]
    if any(k in title for k in consumer_keywords):
        return False

    # 一般的なビジネスキーワード
    base_tob = ["提携", "導入", "開始", "支援", "ソリューション", "開発", "調達", "設立"]
    return any(k in text for k in base_tob)

def fetch_news():
    # PR TIMES スタートアップ & 外食・中堅カテゴリなどから取得
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
st.set_page_config(page_title="toB企業ニュース", layout="wide")
st.title("🏢 toB企業ニュース一覧")

# 初回起動時またはデータがない場合に自動取得
db_file = "news_database.csv"
if not os.path.exists(db_file):
    with st.spinner("初回のニュースを取得中です..."):
        fetch_news()

if os.path.exists(db_file):
    df = pd.read_csv(db_file)
    
    # サイドバー設定
    st.sidebar.header("表示設定")
    if st.sidebar.button("最新ニュースを手動取得"):
        fetch_news()
        st.rerun()

    date_list = sorted(df["date"].unique(), reverse=True)
    selected_date = st.sidebar.selectbox("表示する日付を選択", date_list)

    # 記事表示
    st.subheader(f"📅 {selected_date} の注目のニュース")
    display_df = df[df["date"] == selected_date]
    
    if len(display_df) == 0:
        st.write("この日のtoBニュースはありません。")
    else:
        for _, row in display_df.iterrows():
            st.markdown(f"✅ [{row['title']}]({row['url']})")
else:
    st.warning("ニュースデータがまだありません。「手動取得」ボタンを押すか、自動更新を待ってください。")
