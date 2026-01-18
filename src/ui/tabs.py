import streamlit as st
import datetime
from src.ui.wrappers import (
    run_async, main_ingestion_wrapper, get_feeds_wrapper, delete_feed_wrapper, add_feed_wrapper, 
    seed_data_wrapper, get_papers_by_date_wrapper, get_library_wrapper, toggle_bookmark_wrapper,
    search_wrapper, get_digest_by_date_wrapper, digest_wrapper, get_all_papers_wrapper, get_changelogs_wrapper,
    get_bookmark_status_wrapper, analyze_wrapper
)
from src.ui.components import group_papers_by_category, render_paper_card

def render_sidebar():
    with st.sidebar:
        st.header("Controls")
        if st.button("Fetch Latest Papers"):
            status_container = st.status("Ingesting data...", expanded=True)
            
            def update_status(msg):
                status_container.write(msg)
                
            try:
                stats = run_async(main_ingestion_wrapper(max_papers=5, on_progress=update_status))
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

        st.divider()
        
        with st.expander("Manage RSS Feeds"):
            try:
                feeds = run_async(get_feeds_wrapper())
                st.write(f"**active feeds ({len(feeds)})**")
                for feed in feeds:
                    c1, c2 = st.columns([3, 1])
                    c1.text(feed.name)
                    if c2.button("🗑️", key=f"del_{feed.name}", help=f"Delete {feed.name}"):
                        try:
                            run_async(delete_feed_wrapper(feed.name))
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                
                st.markdown("---")
                st.markdown("**Add New Feed**")
                with st.form("add_feed_form"):
                    new_name = st.text_input("Name (e.g. 'openai')")
                    new_url = st.text_input("RSS URL")
                    if st.form_submit_button("Add Feed"):
                        if new_name and new_url:
                            try:
                                run_async(add_feed_wrapper(new_name, new_url))
                                st.success(f"Added {new_name}")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                        else:
                            st.warning("Name and URL required.")
                            
            except Exception as e:
                st.error(f"Error loading feeds: {e}")

        st.divider()
        
        with st.expander("Admin & Settings"):
            st.markdown("**Database Management**")
            if st.button("Reseed Database (Past 30 Days)", help="Fetches historical data from Arxiv and all Configured RSS Feeds"):
                status_box = st.status("Reseeding database... this may take a minute.", expanded=True)
                
                def log_to_ui(msg):
                    status_box.write(msg)
                    
                try:
                    stats = run_async(seed_data_wrapper(log_to_ui))
                    status_box.update(label="Reseeding Complete!", state="complete", expanded=False)
                    
                    st.success(f"Reseed Finished!\n\n"
                               f"**ArXiv**: {stats['arxiv_new']} new ({stats['arxiv_skipped']} skipped)\n\n"
                               f"**RSS**: {stats['rss_new']} new ({stats['rss_skipped']} skipped)\n\n"
                               f"**Embeddings Created**: {stats['embeddings_created']}")
                               
                except Exception as e:
                    status_box.update(label="Reseeding Failed", state="error")
                    st.error(f"Error: {e}")

def render_feed_tab():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Latest Papers")
    with col2:
        selected_date = st.date_input("Filter by Date", datetime.date.today())
        
    if st.button("Refresh Feed", key="refresh_feed"):
        st.rerun()

    try:
        papers = run_async(get_papers_by_date_wrapper(datetime.datetime.combine(selected_date, datetime.time.min)))
    except Exception as e:
        st.error(f"Error loading papers: {e}")
        papers = []
        
    grouped_papers = group_papers_by_category(papers)
    sorted_cats = sorted(grouped_papers.keys(), key=lambda x: (0 if "Industry" in x else 1, x))

    if not papers:
        st.info("No papers found for this date.")

    for cat in sorted_cats:
        st.markdown(f"### 📂 {cat}")
        for p in grouped_papers[cat]:
            render_paper_card(p, run_async, get_bookmark_status_wrapper, toggle_bookmark_wrapper, analyze_wrapper)
        st.divider()

def render_library_tab():
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

def render_search_tab():
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
                            st.markdown(p.summary_pass_1 or p.abstract, unsafe_allow_html=True)
                            st.markdown(f"[PDF]({p.pdf_url})")
            except Exception as e:
                st.error(f"Search failed: {e}")

def render_digest_tab():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader("Daily Research Digest")
    with c2:
        digest_date = st.date_input("Select Date", datetime.date.today(), key="digest_date")
    
    try:
        digest_dt = datetime.datetime.combine(digest_date, datetime.time.min)
        existing_digest = run_async(get_digest_by_date_wrapper(digest_dt))
        
        if existing_digest:
            st.markdown(existing_digest.markdown_content)
            
            col_download, col_regen = st.columns([1, 1])
            with col_download:
                st.download_button(
                    label="Download as Markdown",
                    data=existing_digest.markdown_content,
                    file_name=f"digest_{digest_date}.md",
                    mime="text/markdown"
                )
            with col_regen:
                if st.button("🔄 Regenerate Digest", help="Re-create digest for this date"):
                    with st.spinner("Regenerating digest..."):
                        new_digest = run_async(digest_wrapper(digest_dt))
                        st.rerun()

        else:
            st.info(f"No digest found for {digest_date}.")
            if st.button(f"Generate Digest for {digest_date}"):
                with st.spinner("Writing blog post..."):
                    new_digest = run_async(digest_wrapper(digest_dt))
                    if new_digest:
                        st.rerun()
                    else:
                        st.warning("Could not generate digest (no papers found for this date?)")

    except Exception as e:
        st.error(f"Digest error: {e}")

def render_archive_tab():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader("Research Archive")
    with c2:
        if st.button("Refresh Archive"):
            st.rerun()

    # --- Filters ---
    with st.expander("Search & Filter", expanded=True):
        col_search, col_filter = st.columns([2, 1])
        with col_search:
            search_query = st.text_input("Search by title or author", placeholder="Type to search...")
        with col_filter:
            pass # placeholder
            
    with st.spinner("Loading archive..."):
        try:
            all_papers = run_async(get_all_papers_wrapper())
            
            if not all_papers:
                st.info("No papers found in the archive.")
            else:
                unique_sources = sorted(list(set(p.source for p in all_papers)))
                with col_filter:
                    selected_sources = st.multiselect("Filter by Source", options=unique_sources, default=None, placeholder="All Sources")
                
                filtered_papers = []
                for p in all_papers:
                    if selected_sources and p.source not in selected_sources:
                        continue
                    if search_query:
                        query = search_query.lower()
                        in_title = query in p.title.lower()
                        in_authors = any(query in a.lower() for a in p.authors)
                        in_abstract = query in p.abstract.lower()
                        if not (in_title or in_authors or in_abstract):
                            continue
                    filtered_papers.append(p)
                
                if not filtered_papers:
                    st.info("No papers match your filters.")
                else:
                    st.caption(f"Showing {len(filtered_papers)} papers")
                    
                    archive_tree = {}
                    for p in filtered_papers:
                        d = p.published_date
                        year = d.year
                        month_name = d.strftime("%B")
                        month_num = d.month
                        day = d.day
                        if year not in archive_tree: archive_tree[year] = {}
                        if month_num not in archive_tree[year]: archive_tree[year][month_num] = {"name": month_name, "days": {}}
                        if day not in archive_tree[year][month_num]["days"]: archive_tree[year][month_num]["days"][day] = []
                        archive_tree[year][month_num]["days"][day].append(p)
                    
                    for year in sorted(archive_tree.keys(), reverse=True):
                        default_expanded = (year == datetime.date.today().year) or (search_query != "")
                        with st.expander(f"📅 **{year}** ({sum(len(d['days'][day]) for m in archive_tree[year] for d in [archive_tree[year][m]] for day in d['days'])})", expanded=default_expanded):
                            months_data = archive_tree[year]
                            for month_num in sorted(months_data.keys(), reverse=True):
                                month_name = months_data[month_num]["name"]
                                st.markdown(f"#### {month_name}")
                                days_data = months_data[month_num]["days"]
                                for day in sorted(days_data.keys(), reverse=True):
                                    st.markdown(f"**{month_name} {day}**")
                                    for p in days_data[day]:
                                        with st.container(border=True):
                                            c1, c2 = st.columns([5,1])
                                            c1.markdown(f"**[{p.source.upper()}]** {p.title}")
                                            meta_text = f"**{', '.join(p.authors)}**"
                                            if p.categories:
                                                meta_text += f" | *{', '.join(p.categories)}*"
                                            c1.caption(meta_text)
                                            if search_query:
                                                 c1.markdown(f"_{p.abstract[:200]}..._")
                                            c2.markdown(f"[Link]({p.pdf_url})")
                                    st.divider()

        except Exception as e:
            st.error(f"Error loading archive: {e}")

def render_changelogs_tab():
    st.header("Software Update Tracker")
    st.info("Tracking updates from OpenAI, ChatGPT, and GitHub Copilot.")
    
    if st.button("Refresh Updates"):
        st.rerun()
        
    try:
        data = run_async(get_changelogs_wrapper())
        col_c, col_o, col_g = st.columns(3)
        
        with col_c:
            st.subheader(f"GitHub Copilot ({len(data.get('copilot', []))})")
            for item in data.get("copilot", []):
                date_str = item['date'].strftime('%Y-%m-%d') if isinstance(item['date'], datetime.datetime) else str(item['date'])
                with st.expander(f"{date_str} - {item['title']}", expanded=True):
                    st.caption(f"[Source]({item['url']})")
                    st.markdown(item['content'])
                    
        with col_o:
            st.subheader(f"OpenAI API ({len(data.get('openai', []))})")
            for item in data.get("openai", [])[:20]:
                 date_str = item['date'].strftime('%Y-%m-%d') if isinstance(item['date'], datetime.datetime) else str(item['date'])
                 with st.expander(f"{date_str} - {item['title'][:40]}...", expanded=True):
                    st.caption(f"[Source]({item['url']})")
                    st.markdown(item['content'])

        with col_g:
            st.subheader(f"ChatGPT ({len(data.get('chatgpt', []))})")
            for item in data.get("chatgpt", []):
                 with st.expander(f"{item['title']}", expanded=True):
                    st.caption(f"[Source]({item['url']})")
                    st.markdown(item['content'])
                    if isinstance(item.get('date'), datetime.datetime):
                        st.caption(f"Date: {item['date'].strftime('%Y-%m-%d')}")

    except Exception as e:
        st.error(f"Failed to fetch changelogs: {e}")
