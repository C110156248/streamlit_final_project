from modules.models import get_response
from modules.search import google_search_results
import streamlit as st
def generate_answer(question, vectorstore, generation_model):
    """生成問題回答，優先從文件資料庫尋找，找不到再進行網路搜尋"""
    doc_context = ""
    web_context = ""
    source_info = []
    
    # 首先從向量數據庫中檢索相關資訊
    found_in_docs = False
    if vectorstore:
        with st.spinner("從文檔中搜尋相關資訊..."):
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            docs = retriever.get_relevant_documents(question)
            
            if docs:
                doc_context = "\n\n".join([doc.page_content for doc in docs])
                source_info.append("文檔資料庫")
                
                # 檢查文檔是否包含足夠相關的資訊
                # 這裡可以加入一個簡單評估，讓模型判斷文檔中是否有足夠的資訊來回答問題
                evaluation_prompt = f"""
                評估以下資訊是否足夠回答問題。
                只回答 "是" 或 "否"。

                資訊:
                {doc_context}

                問題: {question}
                """
                messages = [{"role": "user", "content": evaluation_prompt}]
                evaluation = get_response(messages, model="deepseek-r1:14b").strip().lower()
                
                if "是" in evaluation:
                    found_in_docs = True
                    st.info("在文檔中找到相關資訊")
    
    # 只有在文檔中找不到充分資訊時，才進行網路搜尋
    if not found_in_docs:
        with st.spinner("在文檔中未找到足夠資訊，正在進行網路搜尋..."):
            search_results = google_search_results(question)
            if search_results:
                web_context = "\n\n".join([f"來源 ({result['url']}): {result['content']}" for result in search_results])
                source_info.append("網路搜尋")
    
    # 根據獲取的資訊選擇如何回答
    if doc_context or web_context:
        # 結合文檔和網路搜尋的資訊
        combined_context = ""
        if doc_context:
            combined_context += f"文檔資料:\n{doc_context}\n\n"
        if web_context:
            combined_context += f"網路資料:\n{web_context}"
            
        prompt = f"""基於以下資訊回答問題。如果資訊中沒有完整答案，請考慮所有提供的資訊來提供最全面的回答。
資訊:
{combined_context}

問題: {question}
"""
        messages = [{"role": "user", "content": prompt}]
        answer = get_response(messages, model="EntropyYue/chatglm3:latest")
        source_text = "、".join(source_info)
        return answer, f"從{source_text}中找到"
    
    # 如果都找不到，使用模型直接回答    
    prompt = f"回答以下問題，如果您不確定答案，請誠實地說明: {question}"
    messages = [{"role": "user", "content": prompt}]
    answer = get_response(messages, model="")
    return answer, "使用模型知識直接回答"