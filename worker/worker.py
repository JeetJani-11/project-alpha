import asyncio
from application_sdk.worker import Worker
from application_sdk.clients.utils import get_workflow_client
from app.workflows.github_workflow import GithubIngestWorkflow
from app.activities.github_activities import GithubActivities

APPLICATION_NAME = "default"


async def main():
    # Create Temporal workflow client
    workflow_client = get_workflow_client(application_name=APPLICATION_NAME)
    await workflow_client.load()

    # Instantiate your activities
    activities_instance = GithubActivities()

    # Create worker with workflows + activities
    worker = Worker(
        workflow_client=workflow_client,
        workflow_classes=[GithubIngestWorkflow],
        workflow_activities=activities_instance.get_activities(),
        max_concurrent_activities=5,
    )

    # Start worker (blocking until shutdown)
    await worker.start(daemon=False)


if __name__ == "__main__":
    asyncio.run(main())
