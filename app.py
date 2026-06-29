from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

def load_data():
    file_path = 'master_data.json'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        query = data.get('query', '').lower().strip()
        db = load_data()

        target_lang = ""
        user_input = ""
        
        # 1. Sabse pehle identify karein ki language kaunsi hai
        for lang in db.keys():
            if f"in {lang}" in query:
                target_lang = lang
                user_input = query.replace(f"in {lang}", "").strip()
                break

        if target_lang and target_lang in db:
            lang_data = db[target_lang]
            
            # --- LOGIC A: Full Phrase Matching ---
            # Agar user ne bola "Hello in Odia" aur "hello" phrases mein hai
            if user_input in lang_data.get('phrases', {}):
                result = lang_data['phrases'][user_input]
                return jsonify({
                    "status": "success",
                    "lang": target_lang.upper(),
                    "script": result['script'],
                    "pronounce": result['pronounce']
                })

            # --- LOGIC B: Word Building / Phonetic Parser (Zero Data Gap) ---
            # Agar full phrase nahi mila, toh letters ko jodna shuru karein
            # Example: "ka ma in odia" -> "କମ"
            words = user_input.split() # Input ko "ka", "ma" mein tod dega
            combined_script = ""
            char_map = lang_data.get('characters', {})

            for word in words:
                if word in char_map:
                    combined_script += char_map[word]
                else:
                    # Agar word nahi mila toh wahi word wapas add kar denge
                    combined_script += word 

            if combined_script:
                return jsonify({
                    "status": "success",
                    "lang": target_lang.upper() + " (Phonetic)",
                    "script": combined_script,
                    "pronounce": user_input.capitalize()
                })

        return jsonify({"status": "error", "message": "Language not found or query invalid."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)