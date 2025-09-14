### High-Level Design

The application follows a distributed, message-driven architecture orchestrated by Temporal. The core principle is to separate the workflow's logic (the "what") from the activity's implementation (the "how").

**Flow Diagram:**
`Client (main.py)` -> `Temporal Server` -> `Worker (worker.py)` -> `Workflow (GithubIngestWorkflow)` -> `Activities (GithubActivities)` -> `GitHub API`

### Core Components

1.  **Temporal Workflow (`GithubIngestWorkflow`):**
    -   **Role:** Acts as the orchestrator. It defines the sequence of operations but doesn't contain any business logic itself.
    -   **Responsibilities:**
        -   Starts the process.
        -   Calls the `fetch_repos` activity to get a list of repositories.
        -   Loops through the desired number of repositories and calls the `fetch_repo_commits` activity for each one.
        -   Calls the `publish_to_atlan` activity to format and save the final payload.
    -   **Why:** This makes the entire process resilient. If a worker or activity fails, Temporal can resume the workflow from the last successful step on another worker.

2.  **Temporal Activities (`GithubActivities`):**
    -   **Role:** These are the "workhorses." They contain the actual implementation for each step.
    -   **Key Activities:**
        -   `fetch_repos`: Makes an async API call to GitHub to get all public repositories for an organization.
        -   `fetch_repo_commits`: Fetches the 5 most recent commits for a single repository.
        -   `publish_to_atlan`: Transforms the collected repo and commit data into Atlan-compatible entity payloads and writes them to a JSON file.

### Key Design Decisions

-   **Asynchronous I/O (`aiohttp`):** The GitHub API calls are network-bound and can be slow. Using `aiohttp` allows the application to make multiple HTTP requests concurrently without blocking, significantly speeding up the data extraction process, especially for fetching commits from many repositories.
-   **Decoupled State:** The workflow intentionally avoids holding large amounts of data. State (like the list of repos and commits) is managed by the activities and passed explicitly. The final `publish_to_atlan` activity simulates sending the complete payload to Atlan. This is a scalable pattern, as the state is not tied to a single long-running process.
-   **Configuration Driven:** The workflow is triggered with a simple configuration (`org`, `repo_limit`), making it reusable and easy to trigger with different parameters without changing the code.