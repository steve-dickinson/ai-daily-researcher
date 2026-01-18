import asyncio
import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db.mongo import init_mongo
from src.db.models import DailyDigest

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
BLOG_DIR = os.path.join(DOCS_DIR, "blog")

async def publish_digests():
    print("Initializing Database...")
    await init_mongo()
    
    # Ensure blog directory exists
    os.makedirs(BLOG_DIR, exist_ok=True)
    
    print("Fetching digests...")
    digests = await DailyDigest.find_all().sort("-date").to_list()
    
    if not digests:
        print("No digests found.")
        return

    index_content = "# Daily Research Blog\n\n"
    
    for digest in digests:
        date_str = digest.date.strftime("%Y-%m-%d")
        filename = f"{date_str}.md"
        filepath = os.path.join(BLOG_DIR, filename)
        
        # Add YAML frontmatter for MkDocs if needed, but simple markdown is fine for now.
        # We might want to add a title if the markdown content doesn't have one?
        # The digest markdown usually starts with a title.
        
        with open(filepath, "w") as f:
            f.write(digest.markdown_content)
            
        print(f"Exported: {filename}")
        
        # Add to index
        # Assuming the first line of content is a header, we can use it, or just use date.
        # Let's use the date for now.
        index_content += f"- [{date_str}]({filename})\n"

    # Write Index
    with open(os.path.join(BLOG_DIR, "index.md"), "w") as f:
        f.write(index_content)
        
    print("Blog index generated.")

if __name__ == "__main__":
    asyncio.run(publish_digests())
