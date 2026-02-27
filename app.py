from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# --- Fit Recommendation Engine ---
class FitRecommendationEngine:
    def __init__(self):
        # Size chart example for men's tops
        self.size_chart = {
            'XS': {'chest': (86, 91), 'waist': (71, 76), 'height': (165, 170)},
            'S':  {'chest': (91, 96), 'waist': (76, 81), 'height': (168, 173)},
            'M':  {'chest': (96, 101), 'waist': (81, 86), 'height': (171, 176)},
            'L':  {'chest': (101, 106), 'waist': (86, 91), 'height': (174, 179)},
            'XL': {'chest': (106, 111), 'waist': (91, 96), 'height': (177, 182)},
            'XXL':{'chest': (111, 116), 'waist': (96, 101), 'height': (180, 185)},
        }

        self.body_type_adjustments = {
            'slim': -0.1,
            'athletic': 0,
            'average': 0,
            'curvy': 0.1,
            'plus-size': 0.2
        }

    def recommend_size(self, height_cm, weight_kg, body_type='average', preferred_fit='regular'):
        # Realistic chest/waist estimation using BMI and height
        bmi = weight_kg / ((height_cm/100) ** 2)
        chest = 50 + (bmi - 20) * 1.5 + (height_cm - 170) * 0.3
        waist = 45 + (bmi - 20) * 1.2 + (height_cm - 170) * 0.25
        measurements = {'height': height_cm, 'chest': chest, 'waist': waist}

        scores = {}
        for size, ranges in self.size_chart.items():
            score = 0
            matches = 0
            for m_type, (min_val, max_val) in ranges.items():
                if m_type in measurements:
                    val = measurements[m_type]
                    if min_val <= val <= max_val:
                        score += 1.0
                    elif val < min_val:
                        score += max(0, 1 - (min_val - val) / 10)
                    else:
                        score += max(0, 1 - (val - max_val) / 10)
                    matches += 1
            if matches > 0:
                adj = self.body_type_adjustments.get(body_type.lower(), 0)
                scores[size] = min(1.0, max(0.0, score / matches + adj))

        # Sort sizes by score descending
        sorted_sizes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        recommended = sorted_sizes[0][0]
        confidence = sorted_sizes[0][1]

        # Pick a different alternative size
        alternative = None
        for s, sc in sorted_sizes[1:]:
            if s != recommended:
                alternative = s
                break

        # Adjust recommended size for fit preference
        size_order = list(self.size_chart.keys())
        idx = size_order.index(recommended)
        if preferred_fit.lower() == "loose" and idx < len(size_order) - 1:
            recommended = size_order[idx + 1]
        elif preferred_fit.lower() == "tight" and idx > 0:
            recommended = size_order[idx - 1]

        # Recalculate alternative to ensure it's not the same as recommended
        if alternative == recommended:
            alt_idx = idx + 1 if idx + 1 < len(size_order) else idx - 1
            if 0 <= alt_idx < len(size_order):
                alternative = size_order[alt_idx]

        # Friendly notes
        notes = f"Recommended size: {recommended}. "
        if alternative:
            notes += f"Alternative size: {alternative}. "
        if preferred_fit.lower() == "loose":
            notes += "Since you prefer a loose fit, consider trying the alternative size if unsure."
        elif preferred_fit.lower() == "tight":
            notes += "Since you prefer a tight fit, you may also try the alternative size."

        return {
            "recommended_size": recommended,
            "alternative_size": alternative,
            "confidence": round(confidence, 2),
            "fit_notes": notes
        }

# Instantiate engine
engine = FitRecommendationEngine()

# --- Flask routes ---
@app.route('/')
def index():
    return "Smart Fit Chatbot is running!"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "")

    # Extract height, weight, body type, and fit preference
    height_match = re.search(r'(\d{2,3})\s*cm', message)
    weight_match = re.search(r'(\d{2,3})\s*kg', message)
    body_type_match = re.search(r'(slim|athletic|average|curvy|plus-size)', message.lower())
    fit_match = re.search(r'(loose|tight|regular)', message.lower())

    height = int(height_match.group(1)) if height_match else 175
    weight = int(weight_match.group(1)) if weight_match else 70
    body_type = body_type_match.group(1) if body_type_match else 'average'
    preferred_fit = fit_match.group(1) if fit_match else 'regular'

    result = engine.recommend_size(height, weight, body_type, preferred_fit)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)