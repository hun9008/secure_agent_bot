from pydantic import BaseModel

class user_info(BaseModel):
    info: str

class chat_prompt(BaseModel):
    prev_chat: str
    prompt: str