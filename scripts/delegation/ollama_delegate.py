import requests
import time
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

OLLAMA_API_BASE = "http://localhost:5000/api/ollama"

def submit_workload(prompt: str, params: Optional[dict] = None) -> str:
    """Submit a prompt to the Ollama workload API.

    Args:
        prompt: The input prompt for processing
        params: Optional parameters for model configuration

    Returns:
        str: Task ID for tracking

    Raises:
        HTTPError: If API request fails
    """
    payload = {"prompt": prompt}
    if params:
        payload.update(params)

    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/submit",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()["task_id"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Submission failed: {str(e)}")
        raise

def get_status(task_id: str) -> str:
    """Get current status of a workload task.

    Args:
        task_id: ID of the task to check

    Returns:
        str: Current task status
    """
    try:
        response = requests.get(
            f"{OLLAMA_API_BASE}/status/{task_id}",
            timeout=5
        )
        response.raise_for_status()
        return response.json()["status"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Status check failed: {str(e)}")
        return "error"

def get_result(task_id: str) -> dict:
    """Retrieve final result of a completed task.

    Args:
        task_id: ID of the task to retrieve

    Returns:
        dict: Task result payload

    Raises:
        HTTPError: If API request fails
    """
    try:
        response = requests.get(
            f"{OLLAMA_API_BASE}/result/{task_id}",
            timeout=5
        )
        response.raise_for_status()
        return response.json()["result"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Result retrieval failed: {str(e)}")
        raise

def execute_ollama_workflow(prompt: str, params: Optional[dict] = None) -> dict:
    """Full workflow execution with polling.

    Args:
        prompt: Input prompt for processing
        params: Optional model parameters

    Returns:
        dict: Final processed result
    """
    task_id = submit_workload(prompt, params)
    logging.info(f"Task submitted: {task_id}")

    while True:
        status = get_status(task_id)
        if status == "completed":
            break
        if status == "failed":
            raise RuntimeError(f"Task {task_id} failed")

        logging.info("Task processing...")
        time.sleep(2)

    return get_result(task_id)

if __name__ == "__main__":
    import json
    import sys

    try:
        prompt = sys.argv[1]
        result = execute_ollama_workflow(prompt)
        print(json.dumps(result, indent=2))
    except IndexError:
        print("Usage: python ollama_delegate.py <prompt>")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Workflow failed: {str(e)}")
        sys.exit(1)
