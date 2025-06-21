import os
import time
from datetime import datetime, timedelta
from collections import Counter
import json
import feedparser
import requests
from urllib.parse import urljoin

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# Install required packages if not already installed
required_packages = {
    'feedparser': 'feedparser',
    'requests': 'requests', 
    'dateutil': 'python-dateutil'
}

for package, install_name in required_packages.items():
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {install_name}...")
        os.system(f"pip install {install_name}")

# -------------------
# Google Gemini Configuration
# -------------------
os.environ['GOOGLE_API_KEY'] = 'your api key'

# -------------------
# News Sources & Settings
# -------------------
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml"
]
DB_DIR = './news_vectorstore'
USER_KEYWORDS = ["technology", "science", "politics", "artificial intelligence", "machine learning"]
RECENT_HOURS = 168  # 1 week to ensure we get articles
MIN_CHUNK_WORDS = 20  # Minimum words in a chunk

# -------------------
# Simple RSS Feed Fetcher
# -------------------

def fetch_rss_feed(url, timeout=10):
    """Fetch and parse RSS feed using feedparser directly"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the RSS feed
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse with feedparser
        feed = feedparser.parse(response.content)
        
        documents = []
        for entry in feed.entries:
            # Extract content
            title = getattr(entry, 'title', 'No Title')
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            link = getattr(entry, 'link', '')
            published = getattr(entry, 'published', '')
            
            # Clean and combine content
            content = f"{title}\n\n{summary}" if summary else title
            
            # Create document
            if content and len(content.strip()) > 50:  # Only include substantial content
                doc = Document(
                    page_content=content,
                    metadata={
                        'source': link,
                        'link': link,
                        'title': title,
                        'published': published,
                        'feed_url': url
                    }
                )
                documents.append(doc)
        
        return documents
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

# -------------------
# Ingestion & Preprocessing
# -------------------

def fetch_and_clean():
    all_docs = []
    cutoff = datetime.utcnow() - timedelta(hours=RECENT_HOURS)
    
    for feed_url in RSS_FEEDS:
        print(f"Fetching from: {feed_url}")
        docs = fetch_rss_feed(feed_url)
        print(f"Loaded {len(docs)} articles from {feed_url}")
        all_docs.extend(docs)
    
    # Remove duplicates based on link or title
    unique_docs = {}
    for doc in all_docs:
        # Use link as primary key, title as fallback
        key = doc.metadata.get('link') or doc.metadata.get('title', str(hash(doc.page_content)))
        if key not in unique_docs:
            unique_docs[key] = doc
    
    final_docs = list(unique_docs.values())
    print(f"Total unique articles after deduplication: {len(final_docs)}")
    return final_docs

def split_docs(docs, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = []
    for d in docs:
        try:
            doc_chunks = splitter.split_documents([d])
            for chunk in doc_chunks:
                if len(chunk.page_content.split()) >= MIN_CHUNK_WORDS:
                    chunks.append(chunk)
        except Exception as e:
            print(f"Error splitting document: {e}")
            continue
    return chunks

# -------------------
# Embedding & Storage
# -------------------

def get_vectorstore():
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    except Exception as e:
        print(f"Error creating vectorstore: {e}")
        raise

# -------------------
# Summarization
# -------------------

def summarize_text(docs):
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
        
        # For single document, use direct summarization
        if len(docs) == 1:
            prompt = f"Summarize this news article in 2-3 sentences:\n\n{docs[0].page_content}"
            response = llm.invoke(prompt)
            return response.content
        else:
            # For multiple documents, use chain
            chain = load_summarize_chain(llm, chain_type="map_reduce")
            return chain.run(docs)
    except Exception as e:
        print(f"Error summarizing: {e}")
        # Return first 200 characters as fallback
        return docs[0].page_content[:200] + "..." if docs else "No summary available"

# -------------------
# Sentiment Analysis
# -------------------

def analyze_sentiment(text):
    try:
        prompt = f"""
Analyze the sentiment of this news summary. Respond with exactly one word: Positive, Neutral, or Negative.

Summary: {text}

Sentiment:"""
        
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        response = llm.invoke(prompt)
        sentiment = response.content.strip().split()[0]  # Get first word only
        
        # Ensure valid response
        if sentiment.lower() in ['positive', 'neutral', 'negative']:
            return sentiment.title()
        else:
            return "Neutral"
            
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return "Neutral"

# -------------------
# Topic Clustering / Trend Detection
# -------------------

def detect_trending_topics(chunks, top_n=5):
    words = []
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'her', 'now', 'oil', 'sit', 'way', 'who', 'own', 'say'}
    
    for doc in chunks:
        # Extract meaningful words
        content_words = [
            word.lower().strip('.,!?";()[]{}') 
            for word in doc.page_content.split() 
            if len(word) > 3 and word.lower() not in stop_words and word.isalpha()
        ]
        words.extend(content_words)
    
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_n)]

# -------------------
# Delivery Methods
# -------------------

def deliver_console(items, chunks):
    print("\n" + "="*60)
    print("📰 NEWS ANALYSIS REPORT")
    print("="*60)
    
    if chunks:
        print("\n🔥 TRENDING KEYWORDS:")
        trending = detect_trending_topics(chunks)
        print(", ".join(trending))
    
    print(f"\n📋 TOP {len(items)} NEWS ARTICLES:\n")
    for i, item in enumerate(items, start=1):
        print(f"{i}. {item['summary']}")
        print(f"   💭 Sentiment: {item['sentiment']} | 🏷️ Topic: {item['topic']}")
        print(f"   🔗 Link: {item['url']}\n")

# -------------------
# Main Pipeline
# -------------------

def main():
    try:
        # 1. Ingest & preprocess
        print("📡 Fetching and cleaning news articles...")
        raw_docs = fetch_and_clean()
        
        if not raw_docs:
            print("❌ No articles found. Please check your internet connection and RSS feeds.")
            return
        
        print(f"✅ Found {len(raw_docs)} articles")
        
        # 2. Split documents
        print("📄 Splitting documents into chunks...")
        chunks = split_docs(raw_docs)
        print(f"✅ Created {len(chunks)} chunks")

        if not chunks:
            print("❌ No valid chunks created.")
            return

        # 3. Create vector store
        print("🔍 Creating vector store...")
        store = get_vectorstore()
        store.add_documents(chunks)
        store.persist()
        print("✅ Vector store created")

        # 4. Retrieve relevant documents
        print("🎯 Retrieving relevant documents...")
        profile_query = " ".join(USER_KEYWORDS)
        retriever = store.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": min(10, len(chunks))}
        )
        candidates = retriever.get_relevant_documents(profile_query)
        print(f"✅ Retrieved {len(candidates)} relevant documents")

        # 5. Analyze articles
        print("🧠 Analyzing articles...")
        results = []
        max_articles = min(8, len(candidates))  # Limit to avoid rate limits
        
        for i, doc in enumerate(candidates[:max_articles]):
            print(f"Processing article {i+1}/{max_articles}...")
            try:
                summary = summarize_text([doc])
                sentiment = analyze_sentiment(summary)
                
                # Find matching topic
                summary_lower = summary.lower()
                topic = next(
                    (kw for kw in USER_KEYWORDS if kw.lower() in summary_lower), 
                    "General"
                )
                
                url = doc.metadata.get('source') or doc.metadata.get('link', 'N/A')
                
                results.append({
                    "summary": summary, 
                    "sentiment": sentiment, 
                    "topic": topic, 
                    "url": url
                })
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing document {i+1}: {e}")
                continue

        # 6. Display results
        if results:
            deliver_console(results, chunks)
        else:
            print("❌ No results to display.")

    except Exception as e:
        print(f"💥 An error occurred in main pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
