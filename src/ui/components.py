import streamlit as st
import datetime

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

def render_paper_card(p, run_async_fn, bookmark_wrapper, toggle_bm_wrapper, analyze_wrapper):
    """
    Renders a single paper card.
    Requires async wrappers to be passed in since Streamlit doesn't support async naturally in widgets.
    """
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
            is_bookmarked = run_async_fn(bookmark_wrapper(p.unique_id))
            icon = "❤️" if is_bookmarked else "🤍"
            if st.button(icon, key=f"bk_{p.unique_id}", help="Toggle Bookmark"):
                run_async_fn(toggle_bm_wrapper(p.unique_id))
                st.rerun()

        st.caption(f"**Authors:** {', '.join(p.authors)} | **Published:** {p.published_date.strftime('%Y-%m-%d')}")
        if p.categories:
            st.caption(f"*Tags: {', '.join(p.categories)}*")
        
        with st.expander("Abstract & Analysis", expanded=False):
            st.markdown(f"**Abstract:** {p.abstract}", unsafe_allow_html=True)
            if p.summary_pass_1:
                st.info(f"**AI Summary (Pass 1):**\n{p.summary_pass_1}")
            
            if p.summary_pass_2:
                st.success(f"**Deep Analysis (Pass 2):**\n{p.summary_pass_2}")
            else:
                if st.button(f"Deep Analyze", key=f"analyze_{p.unique_id}"):
                    with st.spinner("Analyzing..."):
                        run_async_fn(analyze_wrapper(p.unique_id))
                        st.rerun()

        st.markdown(f"[Read Full Article]({p.pdf_url})")
