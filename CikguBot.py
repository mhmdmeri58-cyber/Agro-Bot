from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from openai import OpenAI
from dotenv import load_dotenv
import random

# Load environment variables from a .env file
load_dotenv("app.env")

# Initialize the OpenAI client with your API key
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Initialize the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gamification.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Comprehensive persona for Cikgu Bot with a syllabus framework
persona = (
    "You are a helpful and highly experienced assistant named 'Agro Bot'. You act like a plantation field officer who "
    "supports palm oil smallholders with practical, clear, and budget-friendly advice. You explain farming tasks using "
    "simple language, and you give step-by-step instructions that farmers can follow easily.\n\n"
    "Your expertise covers all areas of palm oil cultivation, including detailed guidance on tools and field operations:\n\n"
    "1. Field Tools & Equipment:\n"
    "- Types of common plantation tools: chisel, sickle, dodos, parang, wheelbarrow, sprayer pump (manual/battery), "
    "PPE (gloves, goggles, boots, apron), fertiliser bucket, knapsack sprayer, pole pruner, harvesting pole.\n"
    "- Advanced tools: Cantas machine, telescopic cutter, motorised sprayers, brush cutters, soil augers.\n"
    "- How to choose tools based on palm height, budget, and smallholder needs.\n"
    "- Safe handling procedures for sharp tools.\n"
    "- Basic daily and weekly maintenance: sharpening, cleaning, oiling, adjusting blades, checking bolts.\n\n"
    "2. Pruning & Palm Maintenance (Frond Management):\n"
    "- When and how to prune correctly based on palm age.\n"
    "- Identifying fronds that must be removed and fronds that must be kept.\n"
    "- Step-by-step pruning technique for young palms (0–3 years), mature palms (4–12 years), and tall palms.\n"
    "- Correct angle and position for pruning to avoid damaging the growing point.\n"
    "- How to handle heavy fronds safely to avoid injury.\n"
    "- How pruning affects bunch formation, harvesting efficiency, and pest control.\n\n"
    "3. Harvesting Techniques:\n"
    "- Correct tool selection: chisel for young palms, sickle for taller palms.\n"
    "- Recognising ripe bunches using simple visual cues.\n"
    "- Step-by-step harvesting method: approach, cut, lower bunch safely, loose fruit collection.\n"
    "- Safety tips for tall palms, slippery terrain, and uneven ground.\n"
    "- Maintenance of harvesting tools to ensure clean cuts.\n"
    "- How to reduce FFB losses and increase bunch quality.\n\n"
    "4. Weed Control Tools & Spraying:\n"
    "- Types of sprayers: manual knapsack, motorised, electric.\n"
    "- How to calibrate spray volume and nozzles.\n"
    "- Mixing herbicides safely and correctly.\n"
    "- Proper spraying patterns (circle spraying, selective spraying, path maintenance).\n"
    "- PPE usage and chemical safety.\n"
    "- Cost-saving spraying tips for smallholders.\n\n"
    "5. Fertiliser Application Tools:\n"
    "- Using fertiliser buckets, spreaders, scoops.\n"
    "- Measuring tools (cup method for NPK, borate application techniques).\n"
    "- Step-by-step fertiliser placement around the palm.\n"
    "- Avoiding common wastage mistakes.\n\n"
    "6. Pest & Disease Management Tools:\n"
    "- Pheromone traps for rhinoceros beetle.\n"
    "- Light traps for night pests.\n"
    "- Manual removal tools for infected tissues.\n"
    "- How to identify Ganoderma symptoms using simple field techniques.\n"
    "- Barn owl nest boxes for rat control.\n\n"
    "7. Financial & Practical Advice:\n"
    "- Choosing low-cost tools that still perform well.\n"
    "- When to repair vs when to replace tools.\n"
    "- Recommendations based on smallholder budget.\n\n"
    "Your personality:\n"
    "- Friendly, patient, and very practical — like an experienced plantation supervisor.\n"
    "- Always explains things step-by-step.\n"
    "- Avoids complex scientific terms unless the user asks for them.\n"
    "- Gives affordable and realistic recommendations, not fancy or expensive solutions.\n"
    "- Uses simple language suitable for farmers.\n"
    "- If unsure, you say: 'Hmm, I'm not fully sure, but I can share the normal guidelines used in the field.'\n\n"
    "Your goal:\n"
    "To help palm oil smallholders improve yield, use tools safely, maintain equipment, prune correctly, control weeds, manage pests, "
    "and adopt practical, cost-effective plantation practices."
)

# Define User Model for Gamification Tracking
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)
    stickers = db.Column(db.Text)  # Store stickers as comma-separated values

# Create the database tables
with app.app_context():
    db.create_all()

# Conversation history to maintain context
conversation_history = []

# Flask route for the main page
@app.route("/")
def home():
    return render_template("index_CikguBot.html")

# Function to generate a response for the chatbot
def generate_response(user_input, username):
    global conversation_history
    conversation_history.append({"role": "user", "content": user_input})
    messages = [{"role": "system", "content": persona}] + conversation_history

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )

    bot_response = response.choices[0].message.content.strip()
    conversation_history.append({"role": "assistant", "content": bot_response})

    if len(conversation_history) > 6:
        conversation_history = conversation_history[-6:]

    user = User.query.filter_by(username=username).first()
    if user:
        user.points += 10
        db.session.commit()

    return bot_response

# Flask route for chatbot API
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    username = data.get("username", "guest")

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    response_text = generate_response(user_input, username)
    user = User.query.filter_by(username=username).first()
    return jsonify({"response": response_text, "points": user.points, "stickers": user.stickers})

# Flask route for dynamic quiz generation
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    data = request.json
    topic = data.get("topic", "general science")

    prompt = f"Create a multiple-choice science quiz question for Year 6 students about {topic}. Include 4 answer options and indicate the correct answer."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7,
    )

    quiz_content = response.choices[0].message.content.strip()
    print("Quiz Content:", quiz_content)

    lines = quiz_content.split("\n")
    question = lines[0]
    choices = []
    correct_answer = ""

    for line in lines[1:]:
        line = line.strip()
        if line.lower().startswith("correct answer:") or line.lower().startswith("answer:"):
            correct_answer = line.split(":")[-1].strip()
        elif line and line[0] in "ABCD" and line[1:3] == ") ":
            choices.append(line)

    if not correct_answer:
        print("Warning: No correct answer detected in the response")
    else:
        print("Parsed Correct Answer:", correct_answer)

    print("Parsed Choices:", choices)

    return jsonify({
        "question": question,
        "choices": choices[:4],
        "correct_answer": correct_answer
    })

# ✅ Fixed quiz answer route
@app.route("/quiz_answer", methods=["POST"])
def quiz_answer():
    data = request.json
    user_answer = data.get("answer", "").strip()
    correct_answer = data.get("correct_answer", "").strip()
    username = data.get("username", "guest")  # Read username

    def clean_answer(text):
        return text.lstrip("ABCD) ").strip()

    user_answer_clean = clean_answer(user_answer)
    correct_answer_clean = clean_answer(correct_answer)

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found!", "points": 0})

    if user_answer_clean.lower() == correct_answer_clean.lower():
        user.points += 20
        stickers = user.stickers.split(',') if user.stickers else []
        stickers.append("⭐️")
        user.stickers = ','.join(stickers)
        db.session.commit()
        return jsonify({
            "message": "Correct! You've earned 20 points and a sticker!",
            "points": user.points,
            "stickers": user.stickers
        })

    return jsonify({
        "message": "Oops, that's not correct. Try again!",
        "points": user.points,
        "stickers": user.stickers
    })

# Flask route to clear conversation history
@app.route("/clear", methods=["POST"])
def clear_history():
    global conversation_history
    conversation_history = []
    return jsonify({"message": "Conversation history cleared."})

def reset_user_points():
    with app.app_context():
        users = User.query.all()
        for user in users:
            user.points = 0
            user.stickers = ""
        db.session.commit()

if __name__ == "__main__":
    reset_user_points()
    app.run(debug=True)
