import streamlit as st
import asyncio
import sys
import os

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db.mongo import init_mongo
from src.db.postgres import init_postgres
from src.db.models import Paper
from src.services.research_service import ResearchService

# Initialize Service
service = ResearchService()

# --- Async Helper ---
def run_async(coro):
    return asyncio.run(coro)

async def main_ingestion():
    await init_mongo()
    await init_postgres()
    await service.run_daily_ingestion(max_papers=5)

async def get_recent_papers():
    # Ensure DB is init on the current loop
    await init_mongo()
    await init_postgres()
    # Find last 20 papers
    papers = await Paper.find_all().sort("-published_date").limit(20).to_list()
    return papers

# --- Core Wrappers ---
async def search_wrapper(query: str):
    await init_mongo()
    await init_postgres()
    return await service.search_papers(query, limit=5)

async def digest_wrapper():
    await init_mongo()
    await init_postgres()
    return await service.generate_daily_digest()

async def analyze_wrapper(arxiv_id: str):
    await init_mongo()
    await init_postgres()
    return await service.analyze_paper(arxiv_id)

import datetime

# --- Wrappers for Phase 3 ---
async def toggle_bookmark_wrapper(arxiv_id: str):
    await init_mongo()
    await init_postgres()
    return await service.toggle_bookmark(arxiv_id)

async def get_library_wrapper():
    await init_mongo()
    await init_postgres()
    return await service.get_user_library()

async def get_bookmark_status_wrapper(arxiv_id: str):
    await init_mongo()
    await init_postgres()
    return await service.get_bookmark_status(arxiv_id)

async def get_papers_by_date_wrapper(date):
    await init_mongo()
    await init_postgres()
    return await service.get_papers_by_date(date)

async def get_digest_by_date_wrapper(date):
    await init_mongo()
    await init_postgres()
    return await service.get_digest_by_date(date)

# --- App Layout ---
st.set_page_config(page_title="AI Daily Researcher", layout="wide")
st.title("AI Daily Researcher")

# --- Sidebar ---
with st.sidebar:
    st.header("Controls")
    if st.button("Fetch Latest Papers"):
        status_container = st.status("Ingesting data...", expanded=True)
        
        def update_status(msg):
            status_container.write(msg)
            
        try:
            #Ensure valid loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Since run_daily_ingestion now takes a callback, we need to adapt our wrapper
            async def run_ingest_with_callback():
                await init_mongo()
                await init_postgres()
                return await service.run_daily_ingestion(max_papers=5, on_progress=update_status)
            
            stats = run_async(run_ingest_with_callback())
            
            status_container.update(label="Ingestion Complete!", state="complete", expanded=False)
            
            # Show Source Report
            st.subheader("Daily Source Report")
            for source, count in stats.items():
                if count > 0:
                    st.success(f"**{source.upper()}**: {count} new items")
                else:
                    st.caption(f"{source}: 0 items")
                    
        except Exception as e:
            status_container.update(label="Ingestion Failed", state="error")
            st.error(f"Error: {e}")

# --- Tabs ---
tab_feed, tab_library, tab_search, tab_digest = st.tabs(["Daily Feed", "My Library", "Search", "Daily Digest"])

with tab_feed:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Latest Papers")
    with col2:
        selected_date = st.date_input("Filter by Date", datetime.date.today())
        
    if st.button("Refresh Feed", key="refresh_feed"):
        st.rerun()

    try:
        # Check if date is today, if so use recent, else use date filter
        if selected_date == datetime.date.today():
             papers = run_async(get_recent_papers())
        else:
             papers = run_async(get_papers_by_date_wrapper(datetime.datetime.combine(selected_date, datetime.time.min)))
    except Exception as e:
        st.error(f"Error loading papers: {e}")
        papers = []
        
    # --- Helper Functions ---
    def group_papers_by_category(papers):
        category_map = {
            "cs.AI": "Artificial Intelligence",
            "cs.LG": "Machine Learning",
            "cs.CL": "Computation & Language (NLP)",
            "cs.CV": "Computer Vision",
            "cs.RO": "Robotics",
            "blog": "Industry & Blogs",
            "industry": "Industry & Blogs"
        }
        grouped = {}
        for p in papers:
            primary_cat = "Other"
            if p.categories:
                code = p.categories[0]
                primary_cat = category_map.get(code, code)
                if "blog" in p.categories:
                    primary_cat = "Industry & Blogs"
            
            if primary_cat not in grouped:
                grouped[primary_cat] = []
            grouped[primary_cat].append(p)
        return grouped

    def render_paper_card(p):
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                # Source Badge
                if p.source == "arxiv":
                    st.markdown(f"🔴 **{p.source.upper()}** | **{p.title}**")
                elif p.source in ["openai", "anthropic", "google_deepmind"]:
                    st.markdown(f"🟢 **{p.source.upper()}** | **{p.title}**")
                else: 
                    st.markdown(f"🔵 **{p.source.upper()}** | **{p.title}**")
            
            with c2:
                # Bookmark Toggle
                is_bookmarked = run_async(get_bookmark_status_wrapper(p.unique_id))
                icon = "❤️" if is_bookmarked else "🤍"
                if st.button(icon, key=f"bk_{p.unique_id}", help="Toggle Bookmark"):
                    run_async(toggle_bookmark_wrapper(p.unique_id))
                    st.rerun()

            st.caption(f"**Authors:** {', '.join(p.authors)} | **Published:** {p.published_date.strftime('%Y-%m-%d')}")
            if p.categories:
                st.caption(f"*Tags: {', '.join(p.categories)}*")
            
            with st.expander("Abstract & Analysis", expanded=False):
                st.markdown(f"**Abstract:** {p.abstract}")
                if p.summary_pass_1:
                    st.info(f"**AI Summary (Pass 1):**\n{p.summary_pass_1}")
                
                if p.summary_pass_2:
                    st.success(f"**Deep Analysis (Pass 2):**\n{p.summary_pass_2}")
                else:
                    if st.button(f"Deep Analyze", key=f"analyze_{p.unique_id}"):
                        with st.spinner("Analyzing..."):
                            run_async(analyze_wrapper(p.unique_id))
                            st.rerun()

            st.markdown(f"[Read Full Article]({p.pdf_url})")

    # --- Display Logic ---
    grouped_papers = group_papers_by_category(papers)
    sorted_cats = sorted(grouped_papers.keys(), key=lambda x: (0 if "Industry" in x else 1, x))

    if not papers:
        st.info("No papers found for this date.")

    for cat in sorted_cats:
        st.markdown(f"### 📂 {cat}")
        for p in grouped_papers[cat]:
            render_paper_card(p)
        st.divider()

with tab_library:
    st.subheader("My Library (Bookmarked Papers)")
    if st.button("Refresh Library"):
        st.rerun()
        
    try:
        lib_papers = run_async(get_library_wrapper())
        if not lib_papers:
            st.info("No bookmarks yet. Go to the Feed to add some!")
        
        for p in lib_papers:
            with st.expander(f"{p.title}"):
                st.caption(f"{', '.join(p.authors)}")
                st.markdown(p.abstract)
                if st.button("Remove Bookmark", key=f"rm_{p.unique_id}"):
                    run_async(toggle_bookmark_wrapper(p.unique_id))
                    st.rerun()
    except Exception as e:
        st.error(f"Error loading library: {e}")

with tab_search:
    st.subheader("Semantic Search")
    query = st.text_input("Enter your research question:")
    if query:
        with st.spinner("Searching vector database..."):
            try:
                results = run_async(search_wrapper(query))
                if not results:
                    st.warning("No relevant papers found.")
                else:
                    for p in results:
                        with st.expander(f"{p.title} (Score: High)"):
                            st.markdown(p.summary_pass_1 or p.abstract)
                            st.markdown(f"[PDF]({p.pdf_url})")
            except Exception as e:
                st.error(f"Search failed: {e}")

with tab_digest:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader("Daily Research Digest")
    with c2:
        digest_date = st.date_input("Select Date", datetime.date.today(), key="digest_date")
    
    # Try to fetch existing digest
    try:
        digest_dt = datetime.datetime.combine(digest_date, datetime.time.min)
        existing_digest = run_async(get_digest_by_date_wrapper(digest_dt))
        
        if existing_digest:
            st.markdown(existing_digest.markdown_content)
            st.download_button(
                label="Download as Markdown",
                data=existing_digest.markdown_content,
                file_name=f"digest_{digest_date}.md",
                mime="text/markdown"
            )
        else:
            st.info(f"No digest found for {digest_date}.")
            if digest_date == datetime.date.today():
                if st.button("Generate Today's Digest"):
                    with st.spinner("Writing blog post..."):
                        new_digest = run_async(digest_wrapper())
                        if new_digest:
                            st.rerun()
    except Exception as e:
        st.error(f"Digest error: {e}")
