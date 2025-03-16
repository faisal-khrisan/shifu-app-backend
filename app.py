from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
from dotenv import load_dotenv
import re
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENAI_API_KEY"),
)

@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', '').strip()

        if not ingredients or len(ingredients) < 3:
            return jsonify({'error': 'Please provide at least one valid ingredient'}), 400

        # Prompt to generate structured text and JSON
        prompt = (
            f"""
اكتب وصفة طعام إبداعية باستخدام هذه المكونات: {ingredients}. 
رجاءً اتبع هذا التنسيق بدقة:

اسم الوصفة: (اسم الوصفة)

المكونات:
- (قائمة المكونات)

خطوات الطهي:
1. (خطوات الطهي التفصيلية)

وقت الطهي التقريبي: (عدد الدقائق)

القيمة الغذائية (لكل حصة):
- السعرات الحرارية: (عدد السعرات)
- البروتين: (غرام)
- الدهون: (غرام)
- الكربوهيدرات: (غرام)

ملاحظة: بعد كتابة الوصفة بهذا التنسيق من اليمين الى اليسار ولا تضع اي كلمة انجليزية كلها كلمات عربىة ، قم بإرجاعها أيضًا ككائن JSON بهذا الشكل:
{{
  "recipe_name": "اسم الوصفة",
  "ingredients": ["مكون 1", "مكون 2", "مكون 3"],
  "instructions": ["خطوة 1", "خطوة 2", "خطوة 3"],
  "estimated_time": "عدد الدقائق",
  "nutrition": {{
    "calories": "عدد السعرات",
    "protein": "عدد غرام البروتين",
    "fat": "عدد غرام الدهون",
    "carbs": "عدد غرام الكربوهيدرات"
  }}
}}

أكتب الوصفة أولاً كنص منسق كله باللغة العريية، ثم بعدها JSON. لا تكتب أي شيء آخر.
            """
        )

        completion = client.chat.completions.create(
            model="qwen/qwq-32b:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional chef and nutritionist. Provide clear, practical, daily recipes formatted as required."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=2500
        )

        response_content = completion.choices[0].message.content.strip()

        # Separate the formatted text and JSON

        # Use regex to extract JSON part
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        json_part = ""  # Ensure json_part is always defined

        if json_match:
            json_part = json_match.group(0)
            try:
                recipe_json = json.loads(json_part)
            except json.JSONDecodeError:
                recipe_json = {}  # If JSON is invalid, return empty
        else:
            recipe_json = {}

        # Get the text part (before JSON)
        text_part = response_content.replace(json_part, '').strip() if json_part else response_content

        # Return the response
        return jsonify({
            'formatted_recipe': text_part,
            'recipe_data': recipe_json
        })

    except Exception as e:
        print("DEBUG: Exception:", str(e))  # Log error for debugging
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))


