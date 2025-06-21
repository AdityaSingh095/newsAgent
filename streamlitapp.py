# streamlit_app.py
import streamlit as st
import os
import tempfile
import time
import realnews as news_analyzer  # Import your existing analyzer module

# Configure page
st.set_page_config(
    page_title="News Analyzer Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .header {
        color: #1e3a8a;
        border-bottom: 2px solid #1e3a8a;
        padding-bottom: 10px;
    }
    .article-card {
        background-color: #f8f9fa;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        color: #1f2937 !important;
    }
    .article-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    .article-card h3 {
        color: #1f2937 !important;
        margin-bottom: 15px !important;
        font-size: 18px !important;
    }
    .article-card p {
        color: #374151 !important;
        line-height: 1.6 !important;
        margin-bottom: 0 !important;
    }
    .sentiment-positive {
        color: #059669 !important;
        font-weight: bold;
    }
    .sentiment-negative {
        color: #dc2626 !important;
        font-weight: bold;
    }
    .sentiment-neutral {
        color: #2563eb !important;
        font-weight: bold;
    }
    .keyword-badge {
        background-color: #dbeafe !important;
        color: #1d4ed8 !important;
        border: 1px solid #93c5fd;
        border-radius: 12px;
        padding: 4px 12px;
        margin: 3px;
        display: inline-block;
        font-size: 14px;
        font-weight: 500;
    }
    .stButton>button {
        background-color: #1e40af !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: #1e3a8a !important;
        transform: translateY(-1px) !important;
    }
    .article-button {
        background-color: #1e40af !important;
        color: white !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
    }
    .article-button:hover {
        background-color: #1e3a8a !important;
        transform: translateY(-1px) !important;
        text-decoration: none !important;
    }
    .article-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 15px;
        flex-wrap: wrap;
        gap: 10px;
    }
    .article-meta > div {
        color: #374151 !important;
        font-size: 14px;
    }
    .article-meta strong {
        color: #1f2937 !important;
    }
    .welcome-section {
        text-align: center;
        padding: 40px 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        margin: 20px 0;
    }
    .welcome-section h2 {
        color: #0c4a6e !important;
        margin-bottom: 10px !important;
    }
    .welcome-section p {
        color: #0369a1 !important;
        font-size: 16px !important;
        margin: 5px 0 !important;
    }
    .feature-card {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 20px !important;
        color: #1e293b !important;
    }
    .feature-card strong {
        color: #0f172a !important;
    }
    /* Fix for Streamlit dark mode issues */
    .stMarkdown > div {
        color: inherit;
    }
    /* Ensure proper contrast for all text elements */
    [data-testid="stMarkdownContainer"] p {
        color: #374151 !important;
    }
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: #1f2937 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'trending' not in st.session_state:
    st.session_state.trending = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    st.subheader("API & Settings")
    
    # API Key input
    api_key = st.text_input("Google API Key", type="password", 
                           value=os.environ.get('GOOGLE_API_KEY', ''),
                           help="Get your API key from Google AI Studio")
    
    # RSS Feeds
    st.subheader("RSS Feeds")
    default_feeds = "\n".join(news_analyzer.RSS_FEEDS)
    rss_feeds = st.text_area("Enter RSS URLs (one per line)", 
                            value=default_feeds, 
                            height=200,
                            help="Add or remove news sources to monitor")
    
    # Keywords
    st.subheader("Keywords of Interest")
    default_keywords = ", ".join(news_analyzer.USER_KEYWORDS)
    user_keywords = st.text_input("Enter keywords (comma separated)", 
                                 value=default_keywords,
                                 help="Topics you want to monitor (e.g. AI, politics)")
    
    # Time range
    st.subheader("Time Range")
    recent_hours = st.slider("Analysis window (hours)", 
                            min_value=1, max_value=720, 
                            value=news_analyzer.RECENT_HOURS,
                            help="How far back to look for news articles")
    
    # Run analysis button
    st.markdown("---")
    if st.button("🚀 Analyze News", use_container_width=True):
        st.session_state.processing = True
        st.session_state.results = None
        st.session_state.trending = None
        
        # Update configuration
        news_analyzer.USER_KEYWORDS = [kw.strip() for kw in user_keywords.split(",") if kw.strip()]
        news_analyzer.RSS_FEEDS = [url.strip() for url in rss_feeds.split('\n') if url.strip()]
        news_analyzer.RECENT_HOURS = recent_hours
        
        if api_key:
            os.environ['GOOGLE_API_KEY'] = api_key
        else:
            st.warning("Using default API key. For best results, provide your own key.")

# Main content area
st.title("📰 News Analyzer Dashboard")
st.markdown("Monitor news trends and get AI-powered analysis of the latest articles")

if st.session_state.processing:
    with st.status("Analyzing news sources...", expanded=True) as status:
        try:
            # Create temp directory for vector store
            with tempfile.TemporaryDirectory() as temp_dir:
                news_analyzer.DB_DIR = temp_dir
                st.session_state.results = []
                
                # Execute analysis steps
                st.write("🔍 Fetching and cleaning news articles...")
                raw_docs = news_analyzer.fetch_and_clean()
                
                if not raw_docs:
                    status.update(label="❌ No articles found", state="error")
                    st.error("No articles found. Please check your internet connection and RSS feeds.")
                    st.session_state.processing = False
                    st.stop()
                
                st.write(f"✅ Found {len(raw_docs)} articles")
                
                st.write("📄 Splitting documents into chunks...")
                chunks = news_analyzer.split_docs(raw_docs)
                st.write(f"✅ Created {len(chunks)} chunks")
                
                st.write("🧠 Processing content with AI...")
                # Create vector store
                store = news_analyzer.get_vectorstore()
                store.add_documents(chunks)
                store.persist()
                
                # Retrieve relevant documents
                profile_query = " ".join(news_analyzer.USER_KEYWORDS)
                retriever = store.as_retriever(
                    search_type="similarity", 
                    search_kwargs={"k": min(10, len(chunks))}
                )
                candidates = retriever.get_relevant_documents(profile_query)
                
                # Process each candidate
                results = []
                for i, doc in enumerate(candidates[:8]):  # Limit to 8 articles
                    st.write(f"Analyzing article {i+1}/{min(8, len(candidates))}...")
                    summary = news_analyzer.summarize_text([doc])
                    sentiment = news_analyzer.analyze_sentiment(summary)
                    
                    # Find matching topic
                    summary_lower = summary.lower()
                    topic = next(
                        (kw for kw in news_analyzer.USER_KEYWORDS if kw.lower() in summary_lower), 
                        "General"
                    )
                    
                    url = doc.metadata.get('source') or doc.metadata.get('link', 'N/A')
                    
                    results.append({
                        "summary": summary, 
                        "sentiment": sentiment, 
                        "topic": topic, 
                        "url": url,
                        "title": doc.metadata.get('title', 'Untitled')
                    })
                    time.sleep(1)  # Rate limiting
                
                # Detect trending topics
                st.write("🔥 Identifying trending topics...")
                trending = news_analyzer.detect_trending_topics(chunks, top_n=5)
                
                st.session_state.results = results
                st.session_state.trending = trending
                st.session_state.processing = False
                status.update(label="✅ Analysis complete!", state="complete")
                
        except Exception as e:
            st.session_state.processing = False
            status.update(label="❌ Processing failed", state="error")
            st.error(f"An error occurred: {str(e)}")

# Display results
if st.session_state.results:
    # Display trending topics
    if st.session_state.trending:
        st.subheader("🔥 Trending Topics")
        cols = st.columns(5)
        for i, topic in enumerate(st.session_state.trending):
            cols[i % 5].markdown(f'<div class="keyword-badge">#{topic}</div>', unsafe_allow_html=True)
    
    # Display news articles
    st.subheader(f"📋 Top {len(st.session_state.results)} News Articles")
    
    for i, article in enumerate(st.session_state.results, 1):
        # Sentiment styling
        sentiment_class = {
            "Positive": "sentiment-positive",
            "Negative": "sentiment-negative",
            "Neutral": "sentiment-neutral"
        }.get(article['sentiment'], "")
        
        # Article card
        with st.container():
            st.markdown(f"""
            <div class="article-card">
                <h3>{i}. {article['title'][:80]}{'...' if len(article['title']) > 80 else ''}</h3>
                <p>{article['summary']}</p>
                <div class="article-meta">
                    <div>
                        <strong>Sentiment:</strong> <span class="{sentiment_class}">{article['sentiment']}</span>
                    </div>
                    <div>
                        <strong>Topic:</strong> <span class="keyword-badge">{article['topic']}</span>
                    </div>
                    <div>
                        <a href="{article['url']}" target="_blank" class="article-button">
                            Read Full Article
                        </a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    # Show welcome message and instructions
    if not st.session_state.processing:
        st.markdown("""
        <div class="welcome-section">
            <h2>Welcome to News Analyzer</h2>
            <p>Get AI-powered analysis of trending news topics</p>
            <p>👉 Configure your settings in the sidebar and click "Analyze News" to begin</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.image("https://images.unsplash.com/photo-1588681664899-f142ff2dc9b1?auto=format&fit=crop&w=1200", 
                 caption="News Analysis Dashboard", use_column_width=True)
        
        # Features section
        st.subheader("✨ Features")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="feature-card"><strong>AI Summarization</strong><br><br>Get concise summaries of news articles</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="feature-card"><strong>Sentiment Analysis</strong><br><br>Understand the emotional tone of news</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="feature-card"><strong>Trend Detection</strong><br><br>Identify emerging topics across sources</div>', unsafe_allow_html=True)
        
        st.subheader("How It Works")
        st.markdown("""
        1. **Configure** your news sources and topics in the sidebar
        2. **Click Analyze** to process recent news articles
        3. **Explore** trending topics and article insights
        """)

# Add footer
st.markdown("---")
st.caption("News Analyzer v1.0 | AI-powered news monitoring tool")
