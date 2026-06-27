import json
from openai import AsyncOpenAI
from app.schemas.output import AIOutput

class AIGenerator:
    def __init__(self, api_key: str, model: str, system_prompt: str,
                 base_url: str = "https://api.openai.com/v1",
                 max_output_tokens: int = 350, temperature: float = 0.4):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.system_prompt = system_prompt
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature

    async def generate(self, lead_context: dict, scripts: dict, route_info: dict) -> AIOutput:
        schema = AIOutput.model_json_schema()
        prompt = {
            "lead": lead_context,
            "scripts": scripts,
            "route": route_info,
            "instructions": self.system_prompt
        }

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
            ],
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ai_output",
                    "strict": True,
                    "schema": schema
                }
            }
        )

        data = json.loads(response.choices[0].message.content)
        return AIOutput.model_validate(data)