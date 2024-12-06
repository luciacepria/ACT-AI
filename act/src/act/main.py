import os
from dotenv import load_dotenv
from crew import Act
from flask import Flask, jsonify

# Load environment variables
load_dotenv()

api_key4 = os.getenv('GROQ_API_KEY')

if not api_key4:
    raise RuntimeError("GROQ_API_KEY not set in the environment.")

# Initialize Flask app
app = Flask(__name__)

@app.route('/act', methods=['GET'])
def run():
    inputs = {
        'company_name': 'Tesla',
    }

    crew_instance = Act()

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = crew_instance.crew().kickoff(inputs=inputs)
            return jsonify({"status": "success", "data": result}), 200
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return jsonify({"status": "error", "message": str(e)}), 500

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
