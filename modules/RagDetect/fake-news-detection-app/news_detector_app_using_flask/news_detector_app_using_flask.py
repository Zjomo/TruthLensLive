from flask import Flask, request, jsonify
import joblib
from flask_cors import CORS

import os

# 将工作目录设为当前文件所在目录 
os.chdir(os.path.dirname(os.path.abspath(__file__))) 


# Load model and vectorizer
model = joblib.load("fake_news_model.pkl")
vectorizer = joblib.load("count_vectorizer_for_fake_news_model.pkl")

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

@app.route('/')
def home():
    return "Welcome to the News Classification App!"

@app.route('/predict', methods=['POST'])
def predict():
    # Get JSON data from the request
    data = request.get_json()  # Correct method for JSON body
    text = data.get('text', '')  # Retrieve the 'text' from the JSON body

    if not text:
        return jsonify({"error": "No text provided"}), 400  # Return error if text is missing

    # Preprocess input text using the vectorizer
    vectorized_text = vectorizer.transform([text])

    # Get prediction from the model
    prediction = model.predict(vectorized_text)

    # Map the prediction to "True News" or "Fake News"
    result = "True News" if prediction[0] == 1 else "Fake News"

    # Return prediction as JSON
    return jsonify({"text": text, "prediction": result})

if __name__ == "__main__":
    app.run(debug=True)
