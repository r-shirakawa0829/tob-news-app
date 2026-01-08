import streamlit as st
import feedparser
import pandas as pd
import datetime
import os
import urllib.parse

# --- 判定ロジック：成長意欲のあるtoB企業を抽出 ---
def analyze_growth_company(title, summary):
    text = (title + summary).lower()
    
    # 成長意欲を示すポジティブワード
    growth_keywords = ["採用", "募集", "移転", "増床", "新拠点", "海外展開", "新規事業", "資金調達", "提携", "導入"]
    # 法人向け/ビジネスワード
    biz_keywords = ["法人", "企業", "b2b", "saas", "dx", "ソリューション", "oem", "卸", "加盟", "fc"]

    is_growth = any(k in text for k in growth_keywords)
    is_biz = any(k in text for k in biz_keywords)
    
    return is_growth and is_biz

def fetch_all_sources():
    # 取得ソースのリスト
    feeds = [
        "https://prtimes.jp/index.rdf", # PR TIMES 総合
        "https://prtimes.jp/main/html/searchrlp/ctcd/100/f/rss.xml", # スタートアップ
        # Googleニュースから「採用 強化」「新規事業」などをキーワード検索した結果
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("採用強化 企業") + "&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.google.com/rss/search?q=" + urllib.parse.quote("新サービス 開始") + "&hl=ja&gl=JP&ceid=JP:ja"
    ]
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    new_data = []
    
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if analyze_growth_company(entry.title, entry.summary):
                # 日付取得（Googleニュースの形式にも対応）
                pub_date = today # デフォルトは今日
                if hasattr(entry, 'published'):
                    try:
                        pub_date = pd.to_datetime(entry.published).strftime("%Y-%m-%d")
                    except: pass
                
                new_data.append([pub_date, entry.title, entry.link])
    
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

# --- Streamlit UI ---
st.set_page_config(page_title="成長企業キャッチャー", layout="wide")
st.title("🚀 成長意欲のある企業ニュースまとめ")

db_file = "news_database.csv"
if st.button("最新情報を一括スキャン"):
    with st.spinner("PR TIMES・Googleニュースを巡回中..."):
        count = fetch_all_sources()
        st.success(f"{count}件の成長に関連する記事を更新しました。")
        st.rerun()

col1, col2 = st.columns([1, 2])
with col1:
    selected_date = st.date_input("日付を選択", datetime.date.today())
    target_str = selected_date.strftime("%Y-%m-%d")

with col2:
    st.subheader(f"🔍 {target_str} の成長企業ニュース")
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        display_df = df[df["date"] == target_str]
        if not display_df.empty:
            for _, row in display_df.iterrows():
                # タイトルに特定のワードがあればバッジを表示
                label = ""
                if "採用" in row['title']: label = " 🔥採用強化"
                if "資金調達" in row['title']: label = " 💰資金調達"
                st.markdown(f"✅ **{label}** [{row['title']}]({row['url']})")
        else:
            st.info("データがありません。スキャンを実行してください。")
