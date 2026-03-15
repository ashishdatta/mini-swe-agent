import asyncio
from typing import Any

from pydantic import BaseModel
from swerex.deployment.cloudflare import CloudflareDeployment
from swerex.runtime.abstract import Command as RexCommand

from minisweagent.exceptions import Submitted
from minisweagent.utils.serialize import recursive_merge


class SwerexCloudflareEnvironmentConfig(BaseModel):
    cwd: str = "/"
    timeout: int = 30
    worker_url: str = ""
    worker_api_token: str = ""

class SwerexCloudflareEnvironment:
    def __init__(self, **kwargs) -> None:
        self.config = SwerexCloudflareEnvironmentConfig(**kwargs)
        self.deployment = CloudflareDeployment(
            worker_url=self.config.worker_url,
            worker_api_token=self.config.worker_api_token,
        )
        asyncio.run(self.deployment.start())

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        command = action.get("command", "")
        try:
            result = asyncio.run(
                self.deployment.runtime.execute(
                    RexCommand(
                        command=command,
                        shell=True,
                        check=False,
                        cwd=cwd or self.config.cwd,
                        timeout=timeout or self.config.timeout,
                        merge_output_streams=True,
                    )
                )
            )
            output = {"output": result.stdout, "returncode": result.exit_code, "exception_info": ""}
        except Exception as e:
            output = {
                "output": str(e) if str(e) else "",
                "returncode": -1,
                "exception_info": f"An error occurred while executing the command: {e}",
                "extra": {"exception_type": type(e).__name__, "exception": str(e)},
            }
        self._check_finished(output)
        return output

    def _check_finished(self, output: dict):
        """Raises Submitted if the output indicates task completion."""
        lines = output.get("output", "").lstrip().splitlines(keepends=True)
        if lines and lines[0].strip() == "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" and output["returncode"] == 0:
            submission = "".join(lines[1:])
            raise Submitted(
                {
                    "role": "exit",
                    "content": submission,
                    "extra": {"exit_status": "Submitted", "submission": submission},
                }
            )

    def get_template_vars(self, **kwargs) -> dict[str, Any]:
        return recursive_merge(self.config.model_dump(), kwargs)

    def serialize(self) -> dict:
        return {
            "info": {
                "config": {
                    "environment": self.config.model_dump(mode="json"),
                    "environment_type": f"{self.__class__.__module__}.{self.__class__.__name__}",
                }
            }
        }
