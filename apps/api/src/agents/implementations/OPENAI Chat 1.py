from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class OpenAIChat:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "o1-preview"  # Aangepast naar o1-preview
        
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
