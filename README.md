# RAG 知識問答助手

## 專案簡介

RAG 知識問答助手是一個基於 Retrieval-Augmented Generation (檢索增強生成) 技術的智能問答系統，透過 Streamlit 提供友好的網頁界面。此助手能夠：

![螢幕擷取畫面 2025-06-03 164943](https://github.com/user-attachments/assets/701617f9-8fc0-43e8-9f25-8370ea1741e8)

1. 解讀使用者上傳的文件（PDF、TXT、MD 格式）並回答相關問題
2. 在無法從文件中找到答案時，轉向網路搜尋獲取資訊
3. 利用 gemini-1.5-flash 大型語言模型生成高品質回答

## 功能亮點

- **多重知識來源**：結合文檔、網路搜尋和 AI 模型知識
- **文件處理能力**：支援 PDF、TXT 和 Markdown 格式
- **動態資訊檢索**：先從上傳文檔尋找相關資訊，找不到再使用 Google 搜尋
- **來源透明度**：清晰標示回答資訊來源（文件、網路或模型知識）
- **聊天式界面**：保存對話歷史，提供流暢的使用體驗

## 技術架構

- **大型語言模型**：Google Gemini 1.5 Pro
- **向量嵌入**：Google AI Embeddings
- **向量資料庫**：Facebook AI Similarity Search (FAISS)
- **文本處理**：LangChain 文檔加載器和分割工具
- **網路檢索**：Google Search API 與網頁爬取
- **前端界面**：Streamlit 互動式應用

## 安裝說明

### 環境需求
- Python 3.8+
- 有效的 Google API 金鑰（用於 Gemini AI 和 Embeddings）

### 安裝步驟

1. 克隆儲存庫或下載源碼

2. 安裝必要的依賴套件：
   ```bash
   pip install streamlit langchain langchain-community langchain-google-genai faiss-cpu google-generativeai beautifulsoup4 python-dotenv googlesearch-python requests PyPDF2
   ```

3. 建立 `.env` 文件，加入 Google API 金鑰：
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. 啟動應用：
   ```bash
   streamlit run main.py
   ```

## 使用指南

1. **上傳文件**：
   - 在側邊欄中上傳 PDF、TXT 或 MD 格式文件
   - 點擊「處理文件」按鈕，等待系統處理完成

2. **提問**：
   - 在底部輸入框中輸入您的問題
   - 系統將先從上傳的文件中尋找答案，如無相關資訊則轉向網路搜尋

3. **查看回答**：
   - 系統會顯示回答內容
   - 同時標示資訊來源（文檔、網路或模型知識）

4. **管理對話**：
   - 聊天記錄會自動保存
   - 可點擊「清除聊天記錄」按鈕重新開始對話

## 工作原理

1. **文件處理流程**：
   - 上傳文件後自動進行分塊處理
   - 使用 Google AI Embeddings 將文本轉換為向量
   - 文本分割大小為 1000 字符，重疊 200 字符
   - 向量資料存儲在記憶體中的 FAISS 索引

2. **問答處理流程**：
   - 以相同方式將問題轉換為向量
   - 在向量資料庫中檢索最相似的 3 個文本片段
   - 結合檢索到的上下文生成回答
   - 若無相關片段，則切換到網路搜尋

3. **網路搜尋流程**：
   - 使用 Google Search 獲取相關網頁 URL
   - 爬取網頁內容並提取純文本
   - 清理文本並截取合適長度
   - 結合網頁資訊生成回答

## 注意事項

- 需要穩定的網路連接，特別是進行網路搜尋時
- API 金鑰使用受 Google API 服務條款約束
- 文件處理速度取決於文件大小和複雜度
- 處理特定類型的檔案可能需要安裝額外的套件：
  - 處理 Markdown：`pip install markdown unstructured`

## 錯誤排解

- **嵌入模型錯誤**：確保 `model` 參數設置為 `"embedding-001"`，而非 `"models/embedding-001"`
- **文件載入失敗**：檢查文件編碼，確保使用 UTF-8 或適當的編碼格式
- **記憶體錯誤**：處理大型文件時考慮增加 chunk_size 或減少同時處理的文件數量

## 進階自定義

- 修改 `chunk_size` 和 `chunk_overlap` 以適應不同類型的文檔
- 調整 `search_kwargs={"k": 3}` 中的 k 值以控制檢索文檔數量
- 自定義提示詞模板以優化回答品質

## 未來計劃

- 支持更多文件格式
- 增強網路搜尋結果的相關性
- 添加多語言支援
- 提高處理大型文件的效率
- 整合其他知識來源

---

*此專案使用 Google Gemini API，使用時請遵守 Google 服務條款。*
