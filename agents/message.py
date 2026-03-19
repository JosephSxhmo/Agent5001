from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class AgentMessage(BaseModel):
    sender: str = Field(description="The agent sending the message")
    receiver: str = Field(description="The agent to receive the message")
    instruction: str = Field(description="The core instruction or command")
    context: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary payload data passing between agents")
