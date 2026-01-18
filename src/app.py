import streamlit as st
import sys
import os

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.tabs import (
    render_sidebar, render_feed_tab, render_library_tab, 
    render_search_tab, render_digest_tab, render_archive_tab, 
    render_changelogs_tab
)

# --- App Layout ---
st.set_page_config(page_title="AI Daily Researcher", layout="wide")
st.title("AI Daily Researcher")

# --- Render Sidebar ---
render_sidebar()

# --- Render Tabs ---
tab_feed, tab_library, tab_search, tab_digest, tab_archive, tab_changelogs = st.tabs([
    "Daily Feed", "My Library", "Search", "Daily Digest", "Archive", "Changelogs"
])

with tab_feed:
    render_feed_tab()

with tab_library:
    render_library_tab()

with tab_search:
    render_search_tab()

with tab_digest:
    render_digest_tab()

with tab_archive:
    render_archive_tab()

with tab_changelogs:
    render_changelogs_tab()
