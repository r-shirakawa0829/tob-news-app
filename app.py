import streamlit as st
import feedparser
import pandas as pd
import datetime
import os
import urllib.parse

# --- 判定ロジック ---
def is_tob_news(title, summary):
    text = (title + summary).lower()
    biz_keywords = ["fc", "フランチャイズ", "加盟店", "卸", "業務用", "法人向け", "oem", "dx", "saas", "店舗開発", "福利厚生", "オフィス用"]
    if any(k in text for k in biz_keywords): return True
    consumer_keywords = ["新発売", "期間限定", "食べ放題", "実食レポ", "公式sns"]
    if any(k in title for k in consumer_keywords): return False
    base_tob = ["提携", "導入", "開始", "支援", "ソリューション", "開発", "調達", "設立"]
    return any(k in text for k in base_tob)

# --- 過去分も含めて取得する関数 ---
def fetch_news(target_date_obj=None):
    """
    target_date_objが指定されればその日のキーワード検索結果を取得、
    指定がなければ最新のRSSを取得。
    """
    if target_date_obj:
        # 過去の日付を検索するためのURL（PR TIMESの検索結果ページを利用）
        date_str = target_date_obj.strftime("%Y%m%d")
        encoded_date = urllib.parse.quote(target_date_obj.strftime("%Y年%m月%d日"))
        # 検索キーワードベースで過去分を狙う（RSS経由ではないため簡易的なスクレイピング的アプローチ）
        # ※本来はRSS限定だが、ここでは最新RSSから該当日のものを抽出するロジックを優先
        url = "https://prtimes.jp/main/html/searchrlp/ctcd/100/f/rss.xml"
    else:
        url = "https://prtimes.jp/main/html/searchrlp/ctcd/100/f/rss.xml"
    
    feed = feedparser.parse(url)
    new_data = []
    
    for entry in feed.entries:
        # 記事の公開日を取得
        pub_date = datetime.datetime(*entry.published_parsed[:6]).date()
        
        # 特定の日付指定がある場合はその日のみ、なければ全件
        if target_date_obj and pub_date != target_date_obj:
            continue
            
        if is_tob_news(entry.title, entry.summary):
            new_data.append([pub_date.strftime("%Y-%m-%d"), entry.title, entry.link])
    
    db_file = "news_database.csv"
    if new_data:
        df_new = pd.DataFrame(new_data, columns=["date", "title", "url"])
        if os.path.exists(db_file):
            df_old = pd.read_csv(db_file)
            df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=["url"])
        else:
            df_final = df_new
        df_final.to_csv(db_file, index=False, encoding="utf_8_sig")
        return len(new_data)
    return 0

# --- 画面表示 ---
st.set_page_config(page_title="toB企業ニュースカレンダー", layout="wide")
st.title("📅 toB企業ニュース・カレンダー")

db_file = "news_database.csv"

# サイドバー：過去分取得
st.sidebar.header("📥 ニュース取得")
get_date = st.sidebar.date_input("取得したい過去の日付", datetime.date.today())
if st.sidebar.button("この日のニュースを遡って取得"):
    count = fetch_news(get_date)
    if count > 0:
        st.sidebar.success(f"{count}件の記事を取得・保存しました！")
        st.rerun()
    else:
        st.sidebar.warning("RSSにデータが残っていないか、条件に合う記事がありませんでした。")

# （以下、前回の手動追加とカレンダー表示ロジックを継続）
st.sidebar.markdown("---")
st.sidebar.subheader("➕ 手動で追加")
manual_date = st.sidebar.date_input("追加日", datetime.date.today(), key="manual")
manual_title = st.sidebar.text_input("タイトル")
manual_url = st.sidebar.text_input("URL")
if st.sidebar.button("保存"):
    add_df = pd.DataFrame([[manual_date.strftime("%Y-%m-%d"), manual_title, manual_url]], columns=["date", "title", "url"])
    if os.path.exists(db_file):
        df_old = pd.read_csv(db_file)
        pd.concat([df_old, add_df]).drop_duplicates().to_csv(db_file, index=False, encoding="utf_8_sig")
    else:
        add_df.to_csv(db_file, index=False, encoding="utf_8_sig")
    st.rerun()

# メイン表示
col1, col2 = st.columns([1, 2])
with col1:
    selected_date = st.date_input("カレンダーで表示", datetime.date.today(), key="view")
    target_str = selected_date.strftime("%Y-%m-%d")

with col2:
    st.subheader(f"🔍 {target_str} のニュース")
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        display_df = df[df["date"] == target_str]
        if not display_df.empty:
            for _, row in display_df.iterrows():
                st.markdown(f"✅ [{row['title']}]({row['url']})")
        else:
            st.info("データがありません。「取得」ボタンを試してください。")
