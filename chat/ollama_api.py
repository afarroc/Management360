from ollama import AsyncClient

client = AsyncClient(host='192.168.18.40:11434')

async def generate_response(prompt):
	stream = await client.chat(
		model='deepseek-r1:1.5b', 
		messages=[

			{"role":"user",	"content": prompt}
				],
		stream=True,
		options= {
			"temperature": 0.7,
		  },

	)
	async for chunk in stream:
		print(chunk)
		yield chunk