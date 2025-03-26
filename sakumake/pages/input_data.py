#サクマケアプリ

################################################
#import指定
################################################
from logging import PlaceHolder
import streamlit as st
from openai import OpenAI
import sqlite3
import os

################################################
#レイアウト幅を最大に設定
################################################
st.set_page_config(page_title="サクッとマーケティング情報収集＆検索", layout="wide")


################################################
#APIKey関連
################################################
#Perplexity Key
client_pplx = OpenAI(api_key= os.getenv("YOUR_API_KEY"), base_url="https://api.perplexity.ai")

#GPT Key
#os.environ["OPENAI_API_KEY"] = api_key = os.getenv("OPENAI_API_KEY")

# openAIの機能をclientに代入
client_gpt = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

################################################
#メイン画面
################################################
st.title("外部情報を収集・要約")

tab_titles = ["要約した記事","記事","引用"]
tabs = st.tabs(tab_titles) #（追記）記事要約をtab1に設定

################################################
#サイドバー
################################################
st.sidebar.title("＜条件設定＞")

# 選択肢
keywords = st.sidebar.selectbox("__キーワードを選択__", 
                                ["SNS", "YouTube", "Goolge", "LINE", "SEO", "マーケティングテクノロジー", "フリーワードで調べる"])
if keywords == "フリーワードで調べる" : #分岐
    keywords = st.sidebar.text_input("__キーワードを入力__")

# 設定
info_level = "マーケター向け"

# 記事数
info_count = 5 

# 誰向けの説明か
content_kind_of =[
    "上司向けに説明",
    "部下向けに説明",
    "小学生向けに説明",
]

# 書かせたい内容のテイストを選択肢として表示する
content_kind_of_to_gpt = st.sidebar.selectbox("__要約レベル__",options=content_kind_of)

# chatGPTに出力させる文字数
content_maxStr_to_gpt = str(st.sidebar.slider('__要約文字数__', 100,500,200))

################################################
#初期値、セッション保持の設定
################################################

# 初回ロード時にセッション状態が設定されていない場合はデフォルト値を設定
if 'keywords' not in st.session_state:
    st.session_state.keywords = ""

if 'output_summary' not in st.session_state:
    st.session_state.output_summary = ""

if 're_citations' not in st.session_state:
    st.session_state.re_citations = ""
    
if 'tab_result' not in st.session_state:
    st.session_state.tab_result = ["","","",""]

#初回時はセッションのステータスを0とする    
if 'session_status' not in st.session_state:
    st.session_state.session_status = 0

#初期値設定
article = ""

################################################
#API作法固定
################################################
def query_perplexity(keywords, info_level, info_count):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{keywords} について、最新のマーケティングに関わるニュースを、{info_level}な情報で、{info_count}トピック教えてください。出力は、記事ごとにタイトル・ニュースが掲載された時期・内容に触れた構成で出力してください。"
            ),
        },
    ]
    
    try:
        response = client_pplx.chat.completions.create(
            model="sonar-pro",
            messages=messages,
        )
        return response
    except Exception as e:
        return {"error": str(e)}


################################################
#出力
################################################
info_button = st.sidebar.button("情報を取得する")
if info_button:
    st.session_state.session_status = 1 #セッションのステータスを1に変更する
    result = query_perplexity(keywords, info_level,info_count)
    
    article = result.choices[0].message.content #（追記）出力した記事を変数に設定
    citations = result.citations
    limited_citations = citations[:5] # 最初の5件のURLだけを取得
    re_citations = "  \n".join(f"[{i+1}]{url}" for i , url in enumerate(limited_citations))  #引用記事を見やすく改行
    
    ################################################
    #ChatGPTの部分
    ################################################
    def run_gpt(article,content_kind_of_to_gpt,content_maxStr_to_gpt):
    # リクエスト内容を決める
        request_to_gpt = ("#次の記事を" + content_kind_of_to_gpt + "するために" + 
                    content_maxStr_to_gpt + "字で一つの文章に要約してください" + "#記事：" + article)
    
    # 決めた内容を元にclient.chat.completions.createでchatGPTにリクエスト。オプションとしてmodelにAIモデル、messagesに内容を指定
        response = client_gpt.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": request_to_gpt },
            ],
        )

    # 返って来たレスポンスの内容はresponse.choices[0].message.content.strip()に格納されているので、これをoutput_contentに代入
        output_content = response.choices[0].message.content.strip()
        return output_content # 返って来たレスポンスの内容を返す

    output_summary = run_gpt(article,content_kind_of_to_gpt,content_maxStr_to_gpt)
    st.session_state.output_summary = output_summary
        
    ################################################
    #出力結果
    ################################################
    if isinstance(result, dict) and "error" in result:
        st.error("API 呼び出しエラー: " + result["error"])
    
    else:
        
        ################################################
        #セッションの保持
        ################################################
        st.session_state.keywords = keywords
        st.session_state.output_summary = output_summary
        st.session_state.re_citations = re_citations
        st.session_state.tab_result = [output_summary,article,re_citations,result]

################################################
#出力結果をタブ画面に表示
################################################
with tabs[0]:
    st.write(st.session_state.tab_result[0])

with tabs[1]:
    st.info(st.session_state.tab_result[1]) 

with tabs[2]:
    st.info(st.session_state.tab_result[2]) 

################################################
#SQLiteの内容
################################################

# SQLiteデータベースを作成
conn = sqlite3.connect('sakumake.db') #（修正）db名をsakumake.dbに変更
c = conn.cursor()

# テーブルを作成
c.execute('''CREATE TABLE IF NOT EXISTS information (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, summary TEXT, quote TEXT, rating TEXT)''')

# データベースに変更を保存
conn.commit()
conn.close()

# データベースに接続
conn = sqlite3.connect('sakumake.db')
c = conn.cursor()

# データベースからマーケティング情報一覧を取得する関数
def fetch_information():
    result = c.execute("SELECT * FROM information").fetchall()
    return result

# マーケティング情報一覧を表示
information = fetch_information()
# for row in information:
#     st.write(f"ID: {row[0]}, カテゴリー: {row[1]}, 要約文: {row[2]}, 引用元: {row[3]}, 情報ランク: {row[4]}")

# フォームが送信されたらデータベースに新しい情報を挿入
if st.session_state.session_status == 1: #セッションが1（初回訪問以外）のとき、情報ランクとお気に入りボタンを表示
    st.session_state.rating = st.slider('__お気に入りランク__', 1,5,3)
    favorite_button = st.button("__お気に入り追加__")
    if favorite_button:
        # マーケティング情報の入力フォーム　→（修正）格納データを出力したものに変更
        new_category = st.session_state.keywords
        new_summary = st.session_state.output_summary
        new_quote = st.session_state.re_citations
        new_rating = st.session_state.rating
        
        c.execute("INSERT INTO information (category, summary, quote, rating) VALUES (?, ?, ?, ?)", (new_category, new_summary, new_quote, new_rating))
        conn.commit()
        st.success("__お気に入りに追加されました！__")

# データベース接続をクローズ
conn.close()