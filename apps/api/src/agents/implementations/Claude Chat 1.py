from openai import OpenAI
import base64
import os
from dotenv import load_dotenv
load_dotenv()

def read_pdf(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode("utf-8")

def chat_with_pdf():
    pdf_data = read_pdf("/Users/ewoutdijck/Library/Mobile Documents/com~apple~CloudDocs/Projecten/Claude/PDF Bestanden/FM_Sec12.pdf")
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("Chatbot gestart. Type 'quit' om te stoppen.")
    
    while True:
        user_input = input("\nJouw vraag: ")
        if user_input.lower() == 'quit':
            break
            
        # Stream de response
        message = client.chat.completions.create(
            model="o1-preview",
            stream=True,
            messages=[
                {
                    "role": "system",
                    "content": """Je bent een technische assistent voor trammonteurs. Je taak is om te helpen bij het oplossen van storingen.

BELANGRIJKE REGELS:
- Vul NOOIT aan met eigen technische kennis of tips uit jouw eigen kennis
- Spreek alleen over de reparatie van trams, ga niet in op andere vraagstukken
- Bij het weergeven van oplossingen, doe dit 1 voor 1 en vraag de monteur altijd eerst om een antwoord

- Wees vriendelijk en behulpzaam in je communicatie
- Als een vraag niet beantwoord kan worden met de informatie uit het document, zeg dit dan duidelijk
- Bij twijfel, verwijs altijd naar het officiële document
- Blijf strikt binnen de gegeven documentatie
- !!!!!!!!! LOOP ALTIJD DE PROBLEEM OPLOSSING, stapsgewijs - vraag per vraag DOOR !!!!!!!!!!"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file_content",
                            "file_id": pdf_data,
                            "text": user_input
                        }
                    ]
                }
            ]
        )
        
        # Print de streaming response
        print("\nAssistent:", end=" ")
        for chunk in message:
            if hasattr(chunk.choices[0].delta, 'content'):
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()

if __name__ == "__main__":
    chat_with_pdf()