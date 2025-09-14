import asyncio
import argparse
from application_sdk.clients.temporal import TemporalWorkflowClient
from app.workflows.github_workflow import GithubIngestWorkflow
import json

async def main(args):
    workflow_client = TemporalWorkflowClient(
        host="localhost",
        port=7233,
        namespace="default",
    )
    await workflow_client.load()

    payload = {
        "org": args.org,
        "repo_limit": args.repo_limit,
        "output_file": args.output_file,
    }

    print("Starting workflow with payload:", json.dumps(payload))
    wf = await workflow_client.start_workflow(payload, workflow_class=GithubIngestWorkflow)

    if isinstance(wf, dict):
        print("workflow_id:", wf.get("workflow_id"), "run_id:", wf.get("run_id"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", default="google", help="Github org")
    parser.add_argument("--repo_limit", default=5, type=int, help="How many repos to enrich")
    parser.add_argument("--output_file", default="atlan_payload.json", help="Where to write payloads")
    args = parser.parse_args()
    asyncio.run(main(args))
