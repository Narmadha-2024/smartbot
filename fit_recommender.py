import numpy as np
from typing import Dict, Tuple, List

class FitRecommendationEngine:
    def __init__(self):
        # Size chart mappings (example for tops)
        self.size_charts = {
            'mens_tops': {
                'XS': {'chest': (86, 91), 'waist': (71, 76), 'height': (165, 170)},
                'S': {'chest': (91, 96), 'waist': (76, 81), 'height': (168, 173)},
                'M': {'chest': (96, 101), 'waist': (81, 86), 'height': (171, 176)},
                'L': {'chest': (101, 106), 'waist': (86, 91), 'height': (174, 179)},
                'XL': {'chest': (106, 111), 'waist': (91, 96), 'height': (177, 182)},
                'XXL': {'chest': (111, 116), 'waist': (96, 101), 'height': (180, 185)},
            },
            'womens_tops': {
                'XS': {'bust': (81, 84), 'waist': (61, 64), 'height': (155, 160)},
                'S': {'bust': (84, 88), 'waist': (64, 68), 'height': (158, 163)},
                'M': {'bust': (88, 92), 'waist': (68, 72), 'height': (161, 166)},
                'L': {'bust': (92, 96), 'waist': (72, 76), 'height': (164, 169)},
                'XL': {'bust': (96, 100), 'waist': (76, 80), 'height': (167, 172)},
                'XXL': {'bust': (100, 104), 'waist': (80, 84), 'height': (170, 175)},
            }
        }
        
        self.body_type_adjustments = {
            'slim': -0.5,
            'athletic': 0,
            'average': 0,
            'curvy': 0.5,
            'plus-size': 1
        }
    
    def calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    
    def recommend_size(self, measurements: Dict, gender: str = 'unisex', 
                       category: str = 'tops', body_type: str = 'average') -> Dict:
        
        chart_key = f"{gender}_{category}" if f"{gender}_{category}" in self.size_charts else 'mens_tops'
        size_chart = self.size_charts[chart_key]
        
        scores = {}
        
        for size, ranges in size_chart.items():
            score = 0
            matches = 0
            
            for measurement_type, (min_val, max_val) in ranges.items():
                if measurement_type in measurements:
                    user_val = measurements[measurement_type]
                    if min_val <= user_val <= max_val:
                        score += 1.0
                    elif user_val < min_val:
                        score += max(0, 1 - (min_val - user_val) / 10)
                    else:
                        score += max(0, 1 - (user_val - max_val) / 10)
                    matches += 1
            
            if matches > 0:
                scores[size] = score / matches
        
        adjustment = self.body_type_adjustments.get(body_type, 0)
        
        sorted_sizes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_sizes:
            return {
                'recommended_size': 'M',
                'confidence': 0.5,
                'alternative_size': 'L',
                'fit_notes': 'Unable to determine exact fit. Measurements needed.'
            }
        
        recommended = sorted_sizes[0]
        alternative = sorted_sizes[1] if len(sorted_sizes) > 1 else None
        
        fit_notes = self.generate_fit_notes(recommended[1], body_type)
        
        return {
            'recommended_size': recommended[0],
            'confidence': recommended[1],
            'alternative_size': alternative[0] if alternative else None,
            'fit_notes': fit_notes
        }
    
    def generate_fit_notes(self, confidence: float, body_type: str) -> str:
        if confidence > 0.9:
            base_note = "This should fit you perfectly."
        elif confidence > 0.7:
            base_note = "This should fit well with minor adjustments."
        elif confidence > 0.5:
            base_note = "This size is recommended but consider trying both sizes."
        else:
            base_note = "Fit may vary. Consider ordering multiple sizes."
        
        body_type_notes = {
            'slim': " May have a slightly relaxed fit.",
            'athletic': " Should complement your build well.",
            'curvy': " Consider the fit around bust/hips.",
            'plus-size': " Check the brand's specific plus-size measurements."
        }
        
        return base_note + body_type_notes.get(body_type, "")