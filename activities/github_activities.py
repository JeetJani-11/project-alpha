import aiohttp
from typing import Any, Dict, List
from temporalio import activity
from application_sdk.activities.common.utils import auto_heartbeater
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.activities import ActivitiesInterface
import json

logger = get_logger(__name__)
activity.logger = logger
metrics = get_metrics()
traces = get_traces()


class GithubActivities(ActivitiesInterface):
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.state: Dict[str, Any] = {"repos": [], "commits": {}}

    def get_activities(self) -> List:
        return [
            self.get_workflow_args,
            self.preflight_check,
            self.fetch_repos,
            self.fetch_repo_commits,
            self.publish_to_atlan,
        ]

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_repos(self, workflow_args: Dict[str, Any]) -> Dict[str, Any]:
        org = workflow_args.get("org", "google")
        async with aiohttp.ClientSession(
            headers={"Accept": "application/vnd.github.v3+json"}
        ) as session:
            async with session.get(
                f"{GithubActivities.BASE_URL}/orgs/{org}/repos"
            ) as resp:
                repos = await resp.json()
        self.state["repos"] = repos

        return {
            "total_record_count": len(repos),
            "typename": "github_repo",
            "repos": repos,
        }

    @activity.defn
    async def fetch_repo_commits(self, repo_full_name: str) -> Dict[str, Any]:
        commits_out: List[Dict[str, Any]] = []
        try:
            async with aiohttp.ClientSession(
                headers={"Accept": "application/vnd.github.v3+json"}
            ) as session:
                url = f"{GithubActivities.BASE_URL}/repos/{repo_full_name}/commits?per_page=5"
                async with session.get(url) as resp:
                    commits = await resp.json()

            for c in commits:
                commit_info = {
                    "sha": c.get("sha"),
                    "message": c.get("commit", {}).get("message"),
                    "date": c.get("commit", {}).get("author", {}).get("date"),
                    "author": {
                        "login": (
                            c.get("author", {}).get("login")
                            if c.get("author")
                            else None
                        ),
                        "name": c.get("commit", {}).get("author", {}).get("name"),
                        "email": c.get("commit", {}).get("author", {}).get("email"),
                    },
                }
                commits_out.append(commit_info)

            self.state["commits"][repo_full_name] = commits_out
            return {
                "repo_full_name": repo_full_name,
                "commit_count": len(commits_out),
                "commits": commits_out,
            }
        except Exception as e:
            logger.error("Error fetching commits for %s: %s", repo_full_name, str(e))
            self.state["commits"][repo_full_name] = []
            return {
                "repo_full_name": repo_full_name,
                "commit_count": 0,
                "commits": commits_out,
                "error": str(e),
            }

    @activity.defn
    async def publish_to_atlan(self, workflow_args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            repos = self.state.get("repos", workflow_args.get("repos", []))
            commits_map = self.state.get(
                "commits_map", workflow_args.get("commits_map", {})
            )

            payloads = []
            commit_entity_payloads = []
            for r in repos:
                logger.info("Processing repo: %s", r.get("full_name"))
                print(f"Processing repo: {r.get('full_name')}")
                qn = f"github://{r.get('full_name')}"
                repo_payload = {
                    "typeName": "GitHubRepo",
                    "attributes": {
                        "name": r.get("name"),
                        "qualifiedName": qn,
                        "description": r.get("description"),
                        "url": r.get("html_url"),
                    },
                    "customAttributes": {
                        "stars": r.get("stargazers_count"),
                        "language": r.get("language"),
                        "forks": r.get("forks_count"),
                        "watchers": r.get("watchers_count"),
                    },
                    "relationshipAttributes": {"latestCommits": []},
                }

                repo_commits = commits_map.get(r.get("full_name"), [])
                for c in repo_commits:
                    commit_qn = f"github://{r.get('full_name')}/commit/{c.get('sha')}"
                    repo_payload["relationshipAttributes"]["latestCommits"].append(
                        commit_qn
                    )

                    commit_entity_payloads.append(
                        {
                            "typeName": "GitHubCommit",
                            "attributes": {
                                "qualifiedName": commit_qn,
                                "sha": c.get("sha"),
                                "message": c.get("message"),
                                "date": c.get("date"),
                            },
                            "relationshipAttributes": {
                                "repo": qn,
                                "author": c.get("author", {}).get("login"),
                            },
                        }
                    )
                payloads.append(repo_payload)

            out_payloads = payloads + commit_entity_payloads
            out_path = workflow_args.get("output_path", "atlan_payload.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out_payloads, f, indent=2)
            return {"success": True, "saved_to": out_path, "count": len(out_payloads)}

        except Exception as e:
            logger.error(f"Error in publish_to_atlan: {e}")
            return {"status": "error", "message": str(e)}
