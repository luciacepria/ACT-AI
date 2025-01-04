import time
import os
from dotenv import load_dotenv
from act.crew import Act
from litellm import RateLimitError  # Import specific error type

load_dotenv()

api_key4 = os.getenv('GROQ_API_KEY')

company = "TSLA"

def execute_task_with_retry(task, inputs, max_retries=3, base_delay=3):
    """
    Executes a single task with retry logic.
    """
    retry_delay = base_delay
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to execute task: {task.name}")

            # Set inputs properly (if needed by the task)
            if hasattr(task, "company_name"):
                task.context = inputs  # Option 1: Assign inputs to `context`
            elif hasattr(task, "interpolate_inputs"):
                task.interpolate_inputs(inputs)  # Alternative for passing inputs

            # Execute the task synchronously
            task.execute_sync()

            # Retrieve only the AI-generated output
            result = task.output  # Assuming the task generates output in `output`

            return result
        except RateLimitError as e:
            print(f"Rate limit error on task {task.name}: {e}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        except AttributeError as e:
            print(f"Execution error: {e}")
            break
        except Exception as e:
            print(f"Unexpected error on task {task.name}: {e}")
            break
    else:
        print(f"Task {task.name} failed after maximum retries.")
        return None


def run():
    inputs = {
        'company_name': company,
    }

    # Create the crew instance and get individual tasks
    crew_instance = Act(company)
    tasks = {
        "researcher": crew_instance.researcher_task(),
        "accountant": crew_instance.accountant_task(),
        "recommender": crew_instance.recommender_task(),
        "blogger": crew_instance.blogger_task(),
    }

    results = {}

    # Execute tasks in order and ensure each task is completed before proceeding
    for task_name, task in tasks.items():
        print(f"Starting task: {task_name}")
        # Execute each task and store the output only if the task completes successfully
        result = execute_task_with_retry(task, inputs=inputs)
        if result is not None:
            results[task_name] = result  # Store ONLY the AI-generated output
        else:
            print(f"Skipping {task_name} due to failure.")
            # Skip to the next task but maintain the execution order

    # Print the results of all tasks at the end
    print("\nAll tasks completed. Results:")
    for task_name, result in results.items():
        print(f"\n\n\n ----Result for {task_name}----\n\n\n")
        print(result)  # Print only the AI-generated output


if __name__ == "__main__":
    run()