import openai
import json
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class SmartFitChatbot:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.conversation_history = []
        self.user_profile = {}
        
    def extract_user_info(self, message: str) -> Dict:
        """Extract user measurements and preferences from conversation"""
        prompt = f"""
        Extract the following information from this message if available:
        - Height (in cm or feet/inches)
        - Weight (in kg or lbs)
        - Body type (slim, athletic, average, curvy, plus-size)
        - Preferred fit (tight, regular, loose, oversized)
        - Gender
        - Age
        - Occasion (casual, formal, sports, work)
        - Style preference
        
        Message: {message}
        
        Return as JSON format. Use null for missing values.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a JSON extractor. Only return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            user_info = json.loads(response.choices[0].message.content)
            return user_info
        except:
            return {}
    
    def generate_fit_recommendation(self, user_profile: Dict, product_info: Dict) -> str:
        """Generate personalized fit recommendations"""
        prompt = f"""
        You are a professional fashion consultant specializing in fit recommendations.
        
        User Profile:
        - Height: {user_profile.get('height', 'Not specified')}
        - Weight: {user_profile.get('weight', 'Not specified')}
        - Body Type: {user_profile.get('body_type', 'Not specified')}
        - Preferred Fit: {user_profile.get('preferred_fit', 'Not specified')}
        - Gender: {user_profile.get('gender', 'Not specified')}
        - Age: {user_profile.get('age', 'Not specified')}
        
        Product Information:
        - Type: {product_info.get('type', 'Clothing')}
        - Category: {product_info.get('category', 'General')}
        - Brand: {product_info.get('brand', 'Generic')}
        - Available Sizes: {product_info.get('sizes', 'XS, S, M, L, XL, XXL')}
        
        Provide:
        1. Recommended size
        2. Fit description
        3. Styling tips
        4. Alternative size if between sizes
        5. Any specific considerations
        
        Keep response concise and friendly.
        """
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful fashion fit consultant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content
    
    def chat(self, message: str, product_context: Optional[Dict] = None) -> str:
        self.conversation_history.append({"role": "user", "content": message})
        
        new_info = self.extract_user_info(message)
        self.user_profile.update({k: v for k, v in new_info.items() if v is not None})
        
        if any(keyword in message.lower() for keyword in ['size', 'fit', 'recommend', 'wear', 'measurement']):
            if product_context:
                response = self.generate_fit_recommendation(self.user_profile, product_context)
            else:
                response = self.generate_general_fit_advice()
        else:
            response = self.generate_conversational_response(message)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def generate_general_fit_advice(self) -> str:
        prompt = f"""
        User is asking about fit/sizing. Their profile:
        {json.dumps(self.user_profile, indent=2)}
        
        Recent conversation:
        {self.get_recent_history()}
        
        Provide helpful general sizing advice.
        """
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly fashion consultant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        return response.choices[0].message.content
    
    def generate_conversational_response(self, message: str) -> str:
        system_prompt = """
        You are a friendly fashion and fit consultant chatbot. 
        Help users find their perfect fit.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history[-6:])
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.8,
            max_tokens=200
        )
        
        return response.choices[0].message.content
    
    def get_recent_history(self) -> str:
        recent = self.conversation_history[-4:]
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent])