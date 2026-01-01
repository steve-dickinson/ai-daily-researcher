# AI Daily Researcher

**AI Daily Researcher** is an autonomous, local-first tool that digests the flood of daily AI research. It ingests papers from ArXiv and blog posts from industry leaders (OpenAI, DeepMind, Anthropic), analyzes them using LLMs, and presents them in a streamlined dashboard.

## 🚀 Features

*   **Unified Feed**: Aggregates content from ArXiv (CS.AI, CS.LG, etc.) and major AI labs (RSS Feeds).
*   **AI Summarization**:
    *   **Pass 1**: Quick "tldr" summary for scanning.
    *   **Pass 2 (Deep Analyze)**: Detailed breakdown of methodology and results for interesting papers.
*   **Semantic Search**: Find relevant papers using natural language queries (powered by `pgvector`).
*   **Daily Digest**: Automatically writes a daily blog post summarizing the most important trends.
*   **Personal Library**: Bookmark papers and track what you've read.
*   **Categorization**: Auto-groups papers by field (Vision, NLP, Robotics) and Source (Industry vs. Academia).

## 🛠️ Architecture

The system assumes a single local user and runs entirely in containers:

*   **Frontend**: Streamlit
*   **Backend**: Python 3.13 (Managed by `uv`)
*   **Databases**:
    *   **MongoDB**: Metadata, User Annotations, Digests.
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

1.  **Ingest Data**: Click **"Fetch Latest Papers"** in the sidebar. This pulls fresh data from ArXiv and RSS feeds, summarizes them, and stores embeddings.
2.  **Browse Feed**: View the "Daily Feed" tab. Papers are grouped by category.
3.  **Search**: Use the "Search" tab to ask questions like *"How does chain of thought reasoning work?"*.
4.  **Digest**: Go to "Daily Digest" to see a synthesized blog post of the day's research.

## 🧹 Maintenance

To reset the database (clear all data and schema):
```bash
uv run src/reset_db.py
```
*Note: This deletes all papers, embeddings, and bookmarks.*

## 📄 License
MIT