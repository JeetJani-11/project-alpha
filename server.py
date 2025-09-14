import asyncio
from application_sdk.clients.temporal import TemporalWorkflowClient
from application_sdk.server.fastapi import APIServer, HttpWorkflowTrigger
from application_sdk.observability.logger_adaptor import get_logger
from app.workflows.github_workflow import GithubIngestWorkflow

logger = get_logger(__name__)


async def application_fastapi() -> None:
    workflow_client = TemporalWorkflowClient(
        host="localhost",
        port=7233,
        namespace="default",
    )
    await workflow_client.load()

    app = APIServer(
        ui_enabled=False,
        workflow_client=workflow_client,
    )

    app.register_workflow(
        GithubIngestWorkflow,
        [
            HttpWorkflowTrigger(
                endpoint="/github_ingest",
                methods=["POST"],
                workflow_class=GithubIngestWorkflow,
            )
        ],
    )

    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(application_fastapi())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting...")
