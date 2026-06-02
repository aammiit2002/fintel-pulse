import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


class Agent:
    def __init__(self, name, system_prompt, model="gemini-2.5-flash"):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model

    def run(self, user_content: str) -> str:
        resp = client.models.generate_content(
            model=self.model,
            contents=f"{self.system_prompt}\n\n{user_content}",
        )
        return resp.text
