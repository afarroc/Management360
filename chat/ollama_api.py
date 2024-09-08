from ollama import Client
client = Client(host='192.168.18.40:11434')

def generate_response(prompt):
    stream = client.chat(
        model='gemma2:2b',  # Utiliza el modelo configurado
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )
    for chunk in stream:
        yield chunk['message']['content']

   