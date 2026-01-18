# AI Daily Researcher

**AI Daily Researcher** is an autonomous, local-first tool that digests the flood of daily AI research. It ingests papers from ArXiv and blog posts from industry leaders (OpenAI, DeepMind, Anthropic), analyzes them using LLMs, and presents them in a streamlined dashboard.

## 🚀 Features

*   **Unified Feed**: Aggregates content from ArXiv (CS.AI, CS.LG, etc.) and managed RSS Feeds.
*   **RSS Management**: Dynamically add, remove, and manage industry news sources directly from the UI.
*   **Software Update Tracker**: A dedicated **Changelogs** tab tracking the latest releases from GitHub Copilot, OpenAI API, and ChatGPT.
*   **AI Summarization**:
    *   **Pass 1**: Quick "tldr" summary for scanning.
    *   **Pass 2 (Deep Analyze)**: Detailed breakdown of methodology and results for interesting papers.
*   **Semantic Search**: Find relevant papers using natural language queries (powered by `pgvector`).
*   **Daily Digest**: Automatically writes a daily blog post comparing news and research trends.
*   **Static Blog Site**: Export your Daily Digests to a static website powered by MkDocs.
*   **Personal Library**: Bookmark papers and track what you've read.
*   **Research Archive**: Browse historical data with powerful filters by date, source, and author.

## 🛠️ Architecture

The system assumes a single local user and runs entirely in containers:

*   **Frontend**: Streamlit (Modularized UI components)
*   **Backend**: Python 3.13 (Managed by `uv`)
*   **Databases**:
    *   **MongoDB**: Metadata, User Annotations, Digests, RSS Configs.
    *   **PostgreSQL**: Vector Embeddings (pgvector).
*   **AI Orchestration**: LangChain (Support for OpenAI and Gemini).

## 📦 Installation

### Prerequisites
*   Docker & Docker Compose
*   `uv` (Python package manager)

### Setup
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/ai-daily-researcher.git
    cd ai-daily-researcher
    ```

2.  **Configure Environment**:
    Copy the example env file and add your API keys.
    ```bash
    cp .env.example .env
    # Edit .env and add OPENAI_API_KEY or GEMINI_API_KEY
    ```

3.  **Start Databases**:
    ```bash
    docker-compose up -d
    ```

4.  **Run the App**:
    ```bash
    uv run streamlit run src/app.py
    ```

## 🖥️ Usage

1.  **Ingest Data**: Click **"Fetch Latest Papers"** in the sidebar. This pulls fresh data from ArXiv and your configured RSS feeds.
2.  **Manage Feeds**: Use the sidebar to add new sources (e.g., `https://simonwillison.net/atom/`) or remove existing ones.
3.  **Changelogs**: Check the **"Changelogs"** tab for the latest software updates from major AI providers.
4.  **Search & Archive**: Use Semantic Search for natural language queries or the Archive to filter by metadata.
5.  **Digest**: Go to "Daily Digest" to see a synthesized blog post of the day's research.

### 🌐 Publish Static Blog
You can export your daily digests to a static website for easy sharing:
```bash
# 1. Generate content
uv run python src/publish_digest.py

# 2. Preview site
uv run mkdocs serve

# 3. Deploy to GitHub Pages (optional)
uv run mkdocs gh-deploy
```

## 🧹 Maintenance

To reset the database (clear all data and schema):
```bash
uv run src/reset_db.py
```
*Note: This deletes all papers, embeddings, and bookmarks.*

## 📄 License
MIT