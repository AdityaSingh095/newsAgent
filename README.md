# 📰 News Analyzer Dashboard

An AI-powered autonomous news analysis app built with **Streamlit**, powered by **Google Gemini**, and using **LangChain**, that fetches top news articles from multiple RSS feeds, summarizes them, analyzes sentiment, and detects trending topics based on user preferences.

---

## 🚀 Features

- 🔍 **AI Summarization** – Get concise summaries of news articles using Google Gemini.
- 💬 **Sentiment Analysis** – Understand the emotional tone (Positive/Negative/Neutral) of news.
- 🔥 **Trending Topics** – Automatically extract and highlight top emerging keywords.
- ⚙️ **Customizable** – Choose RSS feeds, keywords, and time window to personalize your analysis.
- 🧠 **Vector Search** – Embeds article content using Gemini embeddings for similarity-based retrieval.

---

## 📦 Folder Structure

```bash
├── streamlitapp.py      # Frontend UI built with Streamlit
├── realnews.py          # Backend logic for news fetching, processing, summarization, sentiment
├── requirements.txt     # Python dependencies
```

---

## 💻 Demo

<p align="center">
  <img src="https://images.unsplash.com/photo-1588681664899-f142ff2dc9b1?auto=format&fit=crop&w=1200" alt="News Analyzer Screenshot" width="600"/>
</p>

---

## 🛠️ Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/news-analyzer.git
cd news-analyzer
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Google Gemini API key

You can set it via environment variable or input it directly in the Streamlit sidebar.

```bash
export GOOGLE_API_KEY=your_api_key_here
```

---

## ▶️ Run the App

```bash
streamlit run streamlitapp.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧠 How It Works

1. **RSS Feed Ingestion** – Articles are fetched from sources like CNN, BBC, Wired, etc.
2. **Text Cleaning & Chunking** – Cleaned and split into text chunks.
3. **Vector Store** – Chunks are embedded using Google Gemini and stored in a vector database.
4. **Similarity Retrieval** – Matches articles with your keywords.
5. **Summarization & Sentiment** – Gemini summarizes each article and detects its sentiment.
6. **Trending Detection** – Analyzes common high-frequency keywords.

---

## 🧪 Example Keywords

```text
technology, artificial intelligence, politics, science, machine learning
```

---

## ✅ Requirements

Make sure the following are installed (automatically handled by `requirements.txt`):

- `streamlit`
- `feedparser`
- `requests`
- `langchain`
- `langchain-google-genai`
- `langchain-community`
- `python-dateutil`

---

## 🧩 Customization

You can edit the following variables inside `realnews.py`:
```python
RSS_FEEDS = [...]  # Add/remove your own feeds
USER_KEYWORDS = [...]  # Personalize the topics
RECENT_HOURS = 72  # Time window for article recency
```

---

---

## 👨‍💻 Author

**Aditya Singh**  
GitHub: [@AdityaSingh095] 
Project powered by Streamlit + Gemini + LangChain  
