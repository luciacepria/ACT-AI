import os
import time
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from act.crew import Act
from litellm import RateLimitError
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message
import yfinance as yf


# Create Flask app
app = Flask(__name__)
CORS(app, support_credentials=True)
# Load environment variables
load_dotenv()



# Global variable to store task results
task_results = {}

# API Key and Company name
api_key4 = os.getenv('GROQ_API_KEY')
company = "TSLA"

app.config['MAIL_SERVER'] = 'smtp.zoho.eu'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'actweb@zohomail.eu'
app.config['MAIL_PASSWORD'] = 'bw0RFe464uWK'

mail= Mail(app)

# Initialize the Crew instance
crew_instance = Act(company)

# Define tasks
tasks = {
    "researcher": crew_instance.researcher_task(),
    "accountant": crew_instance.accountant_task(),
    "recommender": crew_instance.recommender_task(),
    "blogger": crew_instance.blogger_task(),
}

class TaskOutput:
    def __init__(self, task_name, status, data):
        self.task_name = task_name
        self.status = status
        self.data = data

    def to_dict(self):
        return {
            "task_name": self.task_name,
            "status": self.status,
            "data": str(self.data)
        }


@app.route('/send-mail', methods=['POST', 'OPTIONS'])  # Include 'OPTIONS' for pre-flight
@cross_origin(origin='*', methods=['POST', 'OPTIONS'])  # Explicitly allow POST
def send_mail():
    data = request.json
    try:

        # Render the HTML template with data
        html_content = render_template(data['html'], name=data['name'], message=data['message'])

        # Create the message
        msg = Message(data['subject'], sender=app.config['MAIL_USERNAME'], recipients=[data['recipient']])
        msg.body = "This is the plain text body of the email."
        msg.html = html_content  # Assign HTML content
        mail.send(msg)
        return jsonify({'message': 'Mail sent successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/check-status', methods=['GET'])
def check_status():
    return jsonify({'response': 'fjdlk'}), 200


@app.route('/test-html')
def test_html():
    print("Attempting to render the template...")
    try:
        html_content = render_template('signUpMail.html')
        print("Template rendered successfully.")
        return html_content
    except Exception as e:
        print("Failed to render the template.")
        return f"Error rendering template: {str(e)}"


@app.route('/fetch-stock-data', methods=['GET'])
def fetch_stock_data():
    symbol = request.args.get('symbol', 'AAPL')  # Default to Apple Inc if no symbol provided
    period = request.args.get('period', '5d')  # Default period
    interval = request.args.get('interval', '1d')  # Default interval

    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)

        # Extracting numeric data only: timestamps in milliseconds and close prices
        close_prices = [[int(date.timestamp() * 1000), row['Close']]
                        for date, row in hist.iterrows()]

        return jsonify(close_prices)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def execute_task_with_retry(task, inputs, max_retries=3, base_delay=3):
    """
    Executes a single task with retry logic, ensuring TaskOutput is returned.
    """
    retry_delay = base_delay
    for attempt in range(max_retries):
        try:
            if hasattr(task, "company_name"):
                task.context = inputs
            elif hasattr(task, "interpolate_inputs"):
                task.interpolate_inputs(inputs)

            task.execute_sync()

            if not task.output:
                print(f"Warning: Task '{task.name}' output is empty.")
            else:
                return TaskOutput(task_name=task.name, status="success", data=task.output)

        except RateLimitError as e:
            print(f"Rate limit error on task '{task.name}': {e}")
            time.sleep(retry_delay)
            retry_delay *= 2
        except Exception as e:
            print(f"Unexpected error on task '{task.name}': {e}")
            break

    return TaskOutput(task_name=task.name, status="failed", data=None)

@app.route('/task/<task_name>', methods=['POST'])
def run_task(task_name):
    inputs = {'company_name': company}
    try:
        if task_name not in tasks:
            return jsonify({"error": f"Task '{task_name}' not found."}), 404

        task = tasks[task_name]
        result = execute_task_with_retry(task, inputs=inputs)

        return jsonify(result.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/all-tasks', methods=['POST'])
def run_all_tasks():
    """
    Run all tasks in sequence and store their results.
    """
    inputs = {'company_name': company}
    global task_results

    print("Starting execution of all tasks:")
    for task_name, task in tasks.items():
        print(f"Starting task: {task_name}")
        result = execute_task_with_retry(task, inputs=inputs)
        if result.status == "success":
            task_results[task_name] = result
            print(f"Task '{task_name}' completed successfully.")
        else:
            print(f"Skipping task '{task_name}' due to failure.")

    print(f"All task results: {task_results}")
    return jsonify({"message": "All tasks executed successfully"}), 200


@app.route('/all-tasks', methods=['GET'])
def get_all_task_results():
    """
    Retrieve the results of all executed tasks.
    """
    run_all_tasks()
    global task_results
    try:
        # Check if task_results is empty
        if not task_results:
            return jsonify({"message": "No tasks have been executed yet"}), 404

        # Convert each TaskOutput object to a dictionary
        results = {task_name: task_output.to_dict() for task_name, task_output in task_results.items()}

        # Return HTML template if requested
        if request.headers.get('Accept', '').find('text/html') != -1:
            return render_template('allTasks.html', results=results)

        # Return JSON if not requesting HTML
        return jsonify({"results": results}), 200
    except Exception as e:
        print(f"Error in GET /all-tasks: {e}")
        return jsonify({"error": "An unexpected error occurred while fetching task results."}), 500


@app.route('/task/<task_name>', methods=['GET'])
def run_task_get(task_name):
    """
    Retrieves the result of a task based on the task_name.
    """
    try:
        # Check if the task has been executed
        if task_name not in task_results:
            run_all_tasks()
            if task_name not in task_results:
                return jsonify({"error": f"Task '{task_name}' has not been executed yet."}), 404

        # Retrieve the result of the task
        result = task_results[task_name]

        # Return HTML template if requested
        if request.headers.get('Accept', '').find('text/html') != -1:
            return render_template('taskResult.html',
                                   task_name=result.task_name,
                                   status=result.status,
                                   data=result.data)

        # Return JSON if not requesting HTML
        return jsonify(result.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tasks', methods=['GET'])
def list_tasks():
    """
    List all available tasks.
    """
    print("Listing all available tasks...")
    return jsonify({"tasks": list(tasks.keys())}), 200

@app.route('/')
def home():
    """
    Home endpoint to confirm the API is running.
    """
    return jsonify({"message": "Welcome to the Crew Task Execution API!"}), 200

if __name__ == "__main__":
    app.run()