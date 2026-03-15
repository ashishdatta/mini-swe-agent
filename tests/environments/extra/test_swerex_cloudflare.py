import pytest

from minisweagent.environments.extra.swerex_cloudflare import SwerexCloudflareEnvironment
from minisweagent.exceptions import Submitted

WORKER_URL = "https://swerex-cf-container.ashishbdatta.workers.dev"


@pytest.mark.slow
def test_swerex_cloudflare_basic_execution():
    """Test basic command execution in SwerexCloudflareEnvironment."""
    env = SwerexCloudflareEnvironment(worker_url=WORKER_URL)

    result = env.execute({"command": "echo 'hello world'"})

    assert isinstance(result, dict)
    assert "output" in result
    assert "returncode" in result
    assert result["returncode"] == 0
    assert "hello world" in result["output"]


@pytest.mark.slow
def test_swerex_cloudflare_command_failure():
    """Test that command failures are properly captured in SwerexCloudflareEnvironment."""
    env = SwerexCloudflareEnvironment(worker_url=WORKER_URL)

    result = env.execute({"command": "exit 1"})

    assert isinstance(result, dict)
    assert "output" in result
    assert "returncode" in result
    assert result["returncode"] == 1


@pytest.mark.slow
def test_swerex_cloudflare_raises_submitted():
    """Test that execute() raises Submitted when output contains the submission marker."""
    env = SwerexCloudflareEnvironment(worker_url=WORKER_URL)

    with pytest.raises(Submitted) as exc_info:
        env.execute({"command": "printf 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\\nmy patch'"})

    msg = exc_info.value.messages[0]
    assert msg["extra"]["exit_status"] == "Submitted"
    assert "my patch" in msg["extra"]["submission"]
