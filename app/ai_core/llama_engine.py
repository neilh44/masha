from typing import Dict, Any, List, Optional
from datetime import datetime
import groq
import os

class LlamaEngine:
    def __init__(self):
        self.client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3-8b-8192"
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process natural language query using Llama model
        Returns intent and extracted parameters
        """
        prompt = self._create_prompt(query)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        return self._parse_response(response.choices[0].message.content)
    
    def _create_prompt(self, query: str) -> str:
        return f"""
        Extract appointment related information from the following query:
        Query: {query}
        
        Return a JSON with:
        - intent: booking/rescheduling/canceling
        - doctor_name: extracted doctor name
        - date: extracted date
        - time: extracted time
        - patient_name: extracted patient name (if available)
        """
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        # Parse JSON response and return structured data
        try:
            import json
            return json.loads(response)
        except:
            return {
                "intent": None,
                "doctor_name": None,
                "date": None,
                "time": None,
                "patient_name": None
            }
