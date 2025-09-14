from datetime import timedelta
from typing import Any, Dict
from temporalio import workflow
from application_sdk.workflows import WorkflowInterface
from app.activities.github_activities import GithubActivities


@workflow.defn
class GithubIngestWorkflow(WorkflowInterface[GithubActivities]):
    activities_cls = GithubActivities

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]):
        info = workflow.info()
        print(f"Workflow info: {info}")
        print(f"Workflow config: {workflow_config}")

        activities_instance = GithubActivities()
        workflow_args: Dict[str, Any] = await workflow.execute_activity(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(minutes=1),
            task_queue=info.task_queue,
        )
        print(f"Workflow started with config: {workflow_args}")

        config = {
            "org": workflow_args.get("org", "google"),
            "repo_limit": workflow_args.get("repo_limit", 5),
            "output_path": workflow_args.get("output_file", "atlan_payload.json"),
        }

        tq = info.task_queue

        repos_result = await workflow.execute_activity(
            activities_instance.fetch_repos,
            config,
            schedule_to_close_timeout=timedelta(seconds=60),
            task_queue=tq,
        )

        repos_list = repos_result["repos"]
        total_count = repos_result["total_record_count"]
        repo_limit = config.get("repo_limit", 5)

        commits_map = {}
        for r in repos_list[:repo_limit]:
            full_name = r.get("full_name")
            if not full_name:
                continue
            commit_result = await workflow.execute_activity(
                activities_instance.fetch_repo_commits,
                full_name,
                start_to_close_timeout=timedelta(seconds=30),
                task_queue=tq,
            )
            commits_map[full_name] = commit_result.get("commits", [])

        publish_result = await workflow.execute_activity(
            activities_instance.publish_to_atlan,
            {
                "repos": repos_list,
                "commits_map": commits_map,
                "output_path": config["output_path"],
            },
            start_to_close_timeout=timedelta(seconds=60),
            task_queue=tq,
        )

        return {
            "status": "ok",
            "repo_count": total_count,
            "processed_repos": len(repos_list[:repo_limit]),
            "publish_result": publish_result,
        }
