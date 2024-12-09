from openai import OpenAI
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()

class OpenAIChat:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "o1-preview"
        self.pdf_content = None
        
        # Automatisch de PDF laden bij initialisatie
        pdf_path = "/Users/ewoutdijck/Library/Mobile Documents/com~apple~CloudDocs/Projecten/easylog-python-server/apps/api/src/agents/implementations/PDF/BRL SIKB 7000 vs 7_0.pdf"
        self.load_pdf(pdf_path)
        
    def load_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            self.pdf_content = text
            return True
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            return False
        
    def get_chat_response(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            # Return de streaming response
            return response
            
        except Exception as e:
            print(f"Error in getting chat response: {str(e)}")
            return None
    
    def process_message(self, user_message, system_prompt=None):
        messages = []
        
        # Voeg PDF content toe aan de context als deze bestaat
        if self.pdf_content:
            if system_prompt:
                system_prompt = f"{system_prompt}\n\nInhoud van de PDF:\n{self.pdf_content}"
            else:
                system_prompt = f"Inhoud van de PDF:\n{self.pdf_content}"
        
        # Als er een system prompt is, voegen we deze toe als user message
        if system_prompt:
            messages.append({
                "role": "user",
                "content": system_prompt + "\n\n" + user_message
            })
        else:
            # Voeg user message toe
            messages.append({
                "role": "user",
                "content": user_message
            })
        
        # Krijg streaming response
        return self.get_chat_response(messages)

# Voorbeeld gebruik:
if __name__ == "__main__":
    chat = OpenAIChat()
    
    system_prompt = """Je bent een behulpzame AI assistent. 
    Geef duidelijke en beknopte antwoorden."""
    
    while True:
        user_input = input("\nJouw vraag (of 'quit' om te stoppen): ")
        if user_input.lower() == 'quit':
            break
            
        response_stream = chat.process_message(user_input, system_prompt)
        print("\nAssistent:", end=" ")
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print("\n")
