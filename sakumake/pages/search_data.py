import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

################################################
#レイアウト幅を最大に設定
################################################
st.set_page_config(page_title="サクッとマーケティング情報収集＆検索", layout="wide")

# データベースへの接続
engine = create_engine('sqlite:///sakumake.db')

st.title("お気に入り情報検索")

# データベースから選択肢を取得
with engine.connect() as connection:
    # 情報の属性の選択肢を取得
    category_options = pd.read_sql("SELECT DISTINCT category FROM information", connection)['category'].tolist()

################################################
#サイドバー
################################################

# 検索情報設定タイトル
st.sidebar.title("＜条件設定＞")

# Streamlit UIに選択式フィルターを追加
selected_category = st.sidebar.selectbox("__カテゴリーを選択__", options=["すべて"] + category_options)
input_keyword = st.sidebar.text_input("__フリーワードで検索__")

# 検索ボタンが押されたときに実行
if st.sidebar.button("お気に入り情報を検索"):
    # SQLクエリの作成
    query = "SELECT category AS 'カテゴリー', summary AS '要約文', quote AS '引用元', rating AS 'お気に入りランク' FROM information WHERE 1=1"
    if selected_category != "すべて":
        query += f" AND category = '{selected_category}'"
    query += f" AND summary LIKE '%{input_keyword}%'"
    # 情報ランクの降順に並び替え
    query += " ORDER BY rating DESC"    

    # クエリの実行と結果の表示
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)
        df = df.drop(columns=['id'], errors='ignore')  # id列を削除

        # Pandasのカラム幅を制限なく表示する設定
        pd.set_option('display.max_colwidth', None)

        # 静的テーブル表示（セル内全文表示）
        st.table(df)