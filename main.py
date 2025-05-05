import streamlit as st
import os
import tempfile
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import traceback
# 載入環境變數
load_dotenv()

# 設定 Google API 金鑰
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# 初始化 Gemini 模型和 embedding 模型
def init_models():
    generation_model = genai.GenerativeModel('gemini-1.5-pro')
    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY
    )
    return generation_model, embedding_model

# 處理上傳的文件
def process_document(uploaded_file, embedding_model):
    # 創建臨時文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # 根據文件類型選擇對應的 loader
        if uploaded_file.name.endswith('.pdf'):
            loader = PyPDFLoader(tmp_path)
        elif uploaded_file.name.endswith('.txt'):
            loader = TextLoader(tmp_path, encoding="utf-8")
        elif uploaded_file.name.endswith('.md'):
            loader = UnstructuredMarkdownLoader(tmp_path)
        else:
            st.error(f"不支援的文件格式: {uploaded_file.name}")
            os.unlink(tmp_path)
            return None

        # 載入文件
        documents = loader.load()
        
        # 分割文本
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        # 創建向量存儲
        vectorstore = FAISS.from_documents(chunks, embedding_model)
        
        # 清理臨時文件
        os.unlink(tmp_path)
        
        return vectorstore
    
    except Exception as e:
        st.error(f"處理文件時發生錯誤: {str(e)}, 類型: {type(e).__name__}") 
        st.error(f"詳細錯誤{traceback.format_exc()}")
        os.unlink(tmp_path)
        return None

# 使用 Google Search 搜尋相關資訊
def google_search_results(query, num_results=5):
    try:
        search_results = []
        for url in search(query, num_results=num_results):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # 提取文本並清理
                    text = soup.get_text(separator=' ', strip=True)
                    # 移除多餘空白與特殊符號
                    text = re.sub(r'\s+', ' ', text)
                    # 限制文本長度
                    text = text[:1500] + ("..." if len(text) > 1500 else "")
                    search_results.append({
                        "url": url,
                        "content": text
                    })
            except:
                continue
        
        return search_results
    except Exception as e:
        st.error(f"進行 Google 搜尋時發生錯誤: {str(e)}")
        return []

# 生成問題回答
def generate_answer(question, vectorstore, generation_model):
    # 先嘗試從向量數據庫中檢索相關資訊
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        docs = retriever.get_relevant_documents(question)
        
        if docs:
            context = "\n\n".join([doc.page_content for doc in docs])
            prompt = f"""基於以下資訊回答問題。如果資訊中沒有答案，請明確說明您無法從提供的資訊中找到答案。

資訊:
{context}

問題: {question}
"""
            response = generation_model.generate_content(prompt)
            return response.text, "從文檔中找到"
    
    # 如果沒有找到相關資訊，使用 Google Search
    search_results = google_search_results(question)
    if search_results:
        search_context = "\n\n".join([f"來源 ({result['url']}): {result['content']}" for result in search_results])
        prompt = f"""基於以下從網路搜尋到的資訊回答問題。如果資訊中沒有答案，請明確說明您無法找到答案。

資訊:
{search_context}

問題: {question}
"""
        response = generation_model.generate_content(prompt)
        return response.text, "從網路搜尋中找到"
    
    # 如果都找不到，使用模型直接回答
    prompt = f"回答以下問題，如果您不確定答案，請誠實地說明: {question}"
    response = generation_model.generate_content(prompt)
    return response.text, "使用模型知識直接回答"

# Streamlit 應用界面
def main():
    st.title("RAG 知識問答助手")
    st.write("上傳文件並提問，助手會從文件中尋找答案，如果找不到會使用網路搜尋")
    
    # 初始化 session state
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 初始化模型
    generation_model, embedding_model = init_models()
    
    # 側邊欄 - 上傳文件
    with st.sidebar:
        st.header("上傳文件")
        uploaded_file = st.file_uploader("選擇 PDF,TXT,MD 文件", type=['pdf', 'txt', 'md'])
        
        if uploaded_file is not None:
            if st.button("處理文件"):
                with st.spinner("正在處理文件..."):
                    st.session_state.vectorstore = process_document(uploaded_file, embedding_model)
                if st.session_state.vectorstore:
                    st.success(f"文件 '{uploaded_file.name}' 處理完成！")
                    # 重置聊天歷史
                    st.session_state.chat_history = []
        
        if st.button("清除聊天記錄"):
            st.session_state.chat_history = []
    
    # 主視窗 - 聊天介面
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "source" in message and message["source"]:
                st.caption(message["source"])
    
    # 問題輸入
    question = st.chat_input("請輸入您的問題")
    if question:
        # 顯示使用者問題
        with st.chat_message("user"):
            st.write(question)
        
        # 添加到歷史記錄
        st.session_state.chat_history.append({"role": "user", "content": question})
        
        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                answer, source_type = generate_answer(question, st.session_state.vectorstore, generation_model)
                st.write(answer)
                st.caption(source_type)
        
        # 添加到歷史記錄
        st.session_state.chat_history.append({"role": "assistant", "content": answer, "source": source_type})

if __name__ == "__main__":
    main()