# SourceSense: A GitHub Metadata Extractor for Atlan

SourceSense is an Atlan App designed to connect to the GitHub API, extract valuable metadata about an organization's repositories and commits, and structure it for ingestion into the Atlan metadata platform.

This application demonstrates the use of the Atlan Apps Framework and Temporal.io to build robust, scalable metadata ingestion workflows.

---

### Core Features

- **Repository Metadata:** Extracts key information for each repository, including:
  - Basic attributes: Name, description, URL.
  - Custom attributes: Star count, fork count, primary language, and watcher count.
- **Commit Metadata:** Fetches the latest 5 commits for each repository, capturing:
  - SHA, commit message, date, and author.
- **Relationship Extraction:** Establishes lineage by linking each commit back to its parent repository.
- **Scalable Architecture:** Built on Temporal.io, the application can handle rate limiting, retries, and failures gracefully.

---

### Tech Stack

- **Backend:** Python
- **Frameworks:** Atlan Application SDK
- **Orchestration:** Temporal.io
- **API Client:** `aiohttp` for asynchronous HTTP requests

---

### Setup and Installation

**Prerequisites:**
- Python 3.8+
- `uv` (or `pip`) package installer
- A running instance of Temporal.io (see [Temporal's quickstart guide](https://docs.temporal.io/dev-guide/go/getting-started))

**Installation Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-link>
    cd <repository-name>
    ```

2.  **Install dependencies:**
    ```bash
    # Make sure you have uv installed (pip install uv)
    uv pip install -r requirements.txt
    ```

---

### How to Run the App (Demo Instructions)

To run the metadata extraction workflow, you will need two separate terminal windows.

1.  **Start the Temporal Worker:**
    In your first terminal, start the worker process. This worker will listen for tasks from the Temporal server.
    ```bash
    uv run python worker/worker.py
    ```
    You should see output indicating the worker has started and is listening for activities.

2.  **Trigger the Workflow:**
    In your second terminal, run the `main.py` script to start the workflow. You can customize the target organization and the number of repositories to process.
    ```bash
    # Run with default settings (org=google, repo_limit=5)
    uv run python main.py

    # Run for a different organization
    uv run python main.py --org "apache" --repo_limit 10
    ```

3.  **Check the Output:**
    The workflow will execute, and you will see logs in both the worker and main script terminals. Upon completion, a file named `atlan_payload.json` will be created in the root directory containing the extracted metadata.