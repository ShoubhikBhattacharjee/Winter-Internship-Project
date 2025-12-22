# Documentation Structure: Notes and Indexing

## The Notes Folder
The `Notes/` folder is the primary storage for all detailed knowledge base documents. Each file here contains the full context and technical details for a specific topic.

## File Connectivity
This file (`vector_db.md`) is linked to the `kb.json` file. The JSON acts as a searchable index, while this Markdown file provides the source depth required for accurate RAG (Retrieval-Augmented Generation).

## System Requirements
- **Format:** All source files should use the `.md` extension.
- **Pathing:** The system uses relative paths (e.g., `./Notes/vector_db.md`) to ensure the database remains functional across different environments.
- **Metadata:** When the "Fetcher" script runs, it looks for the content in this file to supplement the short answer provided in the JSON.s