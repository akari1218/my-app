
import streamlit as st
from gtts import gTTS
import io
import re
import json
import os
from deep_translator import GoogleTranslator

# ページ設定
st.set_page_config(layout="wide", page_title="Shadowing App")

# --- ファイル保存の設定 ---
SAVE_FILE = "custom_topics_v3.json"

def load_topics():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_topic(title, en_content, ja_content):
    topics = load_topics()
    topics[title] = {"en": en_content, "ja": ja_content}
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=4)

@st.cache_data
def get_translation(text):
    try:
        return GoogleTranslator(source='en', target='ja').translate(text)
    except Exception:
        return "※翻訳を取得できませんでした"

def split_text(text):
    if not text:
        return []
    parts = re.split(r'\n|/|(?<=。)\s+', text)
    return [p.strip() for p in parts if p.strip()]

# 🌟 共通の学習スタート処理 🌟
def start_learning(en_text, ja_text):
    sentences_list = split_text(en_text)
    translations_list = split_text(ja_text)
    if sentences_list:
        final_translations = translations_list
        if len(translations_list) != len(sentences_list):
            with st.spinner("自動翻訳を生成中..."):
                final_translations = [get_translation(s) for s in sentences_list]
        st.session_state.sentences = sentences_list
        st.session_state.translations = final_translations
        st.session_state.current_index = 0
        st.session_state.is_playing = True
        st.rerun()
    else:
        st.error("有効な英文がありません。")

# --- セッションステートの初期化 ---
if "sentences" not in st.session_state:
    st.session_state.sentences = []
if "translations" not in st.session_state:
    st.session_state.translations = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False

st.title("🗣️ 英語シャドーイング学習アプリ")

# 📂 トピックの読み込み（サイドバーを使わず、ここで読み込みます）
custom_topics = load_topics()
all_topics = {"📝 新規作成 (直接入力)": {"en": "", "ja": ""}}
all_topics.update(custom_topics)

# メイン画面のタブ
tab_play, tab_edit = st.tabs(["🎧 学習プレイ画面", "📝 文章の入力・編集"])

# ==========================================
# タブ1：学習プレイ画面
# ==========================================
with tab_play:
    # 🌟 トピック選択とスタートボタンをタブ内に横並びで配置 🌟
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        selected_play_topic = st.selectbox("📂 学習するトピックを選択:", list(all_topics.keys()), key="play_topic")
    with col_t2:
        # ボタンの高さを選択欄と合わせるための調整
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 このトピックで開始 / 切替", key="play_start", use_container_width=True, type="primary"):
            start_learning(all_topics[selected_play_topic]["en"], all_topics[selected_play_topic]["ja"])
    
    st.markdown("---")

    if st.session_state.is_playing and st.session_state.sentences:
        current_sentence = st.session_state.sentences[st.session_state.current_index]
        current_translation = st.session_state.translations[st.session_state.current_index]
        
        total_len = len(st.session_state.sentences)
        st.caption(f"進行状況: {st.session_state.current_index + 1} / {total_len}")
        st.markdown(f"## {current_sentence}")
        st.info(f"🇯🇵 **訳:** {current_translation}")
        
        try:
            tts = gTTS(text=current_sentence, lang='en')
            sound_fp = io.BytesIO()
            tts.write_to_fp(sound_fp)
            st.audio(sound_fp, format='audio/mp3', autoplay=True) 
        except Exception as e:
            st.error(f"音声エラー: {e}")
        
        st.markdown("---")
        
        # 操作ボタン
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.session_state.current_index > 0:
                if st.button("⬅ ひとつ前へ", use_container_width=True):
                    st.session_state.current_index -= 1
                    st.rerun()
            else:
                st.button("⬅ ひとつ前へ", use_container_width=True, disabled=True)
        with col2:
            if st.button("🔄 もう一度再生", use_container_width=True):
                st.rerun()
        with col3:
            if st.session_state.current_index + 1 < total_len:
                if st.button("次へ進む ➡", use_container_width=True):
                    st.session_state.current_index += 1
                    st.rerun()
            else:
                if st.button("🎉 最初からやり直す", use_container_width=True):
                    st.session_state.current_index = 0
                    st.rerun()
    else:
        st.info("上の「開始 / 切替」ボタンを押すと学習が始まります。")

# ==========================================
# タブ2：文章の入力・編集画面
# ==========================================
with tab_edit:
    st.info("💡 英文と和訳を自由に編集できます。既存のトピックを直したい場合は、下から呼び出してください。")
    
    # 🌟 編集タブ内でも、編集したいトピックを選べるようにしました 🌟
    selected_edit_topic = st.selectbox("📂 編集・確認するトピックを呼び出す:", list(all_topics.keys()), key="edit_topic")
    
    default_en = all_topics[selected_edit_topic]["en"]
    default_ja = all_topics[selected_edit_topic]["ja"]

    st.markdown("---")
    
    col_en_input, col_ja_input = st.columns(2)
    with col_en_input:
        text_input_en = st.text_area("学習する英文:", value=default_en, height=400, key="edit_en")
    with col_ja_input:
        text_input_ja = st.text_area("対応する日本語訳:", value=default_ja, height=400, key="edit_ja")
    
    sentences_list = split_text(text_input_en)
    translations_list = split_text(text_input_ja)
    en_count = len(sentences_list)
    ja_count = len(translations_list)

    st.markdown(f"📊 **現在の文章数:** 英文 {en_count} 文 / 和訳 {ja_count} 文")
    
    # トピック保存
    st.markdown("---")
    st.subheader("💾 この内容をトピックとして保存")
    save_col1, save_col2 = st.columns([3, 1])
    with save_col1:
        save_name = st.text_input("トピック名:", value=selected_edit_topic if selected_edit_topic != "📝 新規作成 (直接入力)" else "", key="save_name_input")
    with save_col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📁 保存", use_container_width=True):
            if save_name and text_input_en:
                save_topic(save_name, text_input_en, text_input_ja)
                st.success(f"「{save_name}」を保存しました！")
                st.rerun()
            else:
                st.error("名前と英文が必要です。")

    st.markdown("---")
    if st.button("🚀 この編集内容で学習をスタート", key="edit_start_bottom", use_container_width=True, type="primary"):
        start_learning(text_input_en, text_input_ja)
        # --- 使い方ガイド（折りたたみ式） ---
with st.expander("ℹ️ 初めての方へ：このアプリの使い方ガイド", expanded=True):
    st.markdown("""
    ### 🛠️ 3ステップで始める使い方
    1. **文章を準備する（まずはここから！）**
        - 「**📝 文章の入力・編集**」タブを開きます。
        - 好きな英文と日本語訳を入力して、下にある「**📁 保存**」ボタンを押して保存します。
    2. **トピックを選ぶ**
        - 「**🎧 学習プレイ画面**」タブに戻ります。
        - 「📂 学習するトピックを選択:」から、先ほど保存した名前を選びます。
    3. **学習スタート！**
        - 「**🚀 このトピックで開始 / 切替**」ボタンを押すと、1文ずつ音声が自動再生されます。
        - 音声を追いかけるように発音（シャドーイング）してみましょう！
    
    ---
    💡 *使い方がわかったら、このパネルの右上にある「▲」を押すと画面をスッキリさせられます。*
    """)
    # --- セッションステートの初期化 ---
if "sentences" not in st.session_state:
    st.session_state.sentences = []
if "translations" not in st.session_state:
    st.session_state.translations = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False
# 👇 ここを1行追加！
if "guide_seen" not in st.session_state:
    st.session_state.guide_seen = False
    # --- 初回ポップアップガイド ---
@st.dialog("👋 ようこそ！英語シャドーイングアプリへ")
def show_welcome_guide():
    st.markdown("""
    このアプリは、あなたの好きな英文でシャドーイング（音声の後を追って発音する練習）ができるアプリです。
    
    ### 📝 かんたんな使い方
    1. 「**📝 文章の入力・編集**」タブで英文と和訳を入力して保存する。
    2. 「**🎧 学習プレイ画面**」タブで保存したトピックを選ぶ。
    3. 「**🚀 開始**」ボタンを押すと、自動で音声が流れます！
    """)
    if st.button("使い方を理解したので始める！", type="primary", use_container_width=True):
        st.session_state.guide_seen = True
        st.rerun()

# まだガイドを見ていない場合だけポップアップを表示
if not st.session_state.guide_seen:
    show_welcome_guide()
    