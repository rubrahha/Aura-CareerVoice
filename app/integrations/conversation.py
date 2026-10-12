"""Conversation manager adapted from lythelab/voice-agent-starter-kit.

Original upstream: app/pipeline/conversation.py (MIT, copyright 2026 lythe labs).
Adaptation: take system/instruction prompts as arguments instead of depending on
upstream app.config settings; avoid retaining chat data beyond a request.
See THIRD_PARTY_NOTICES.md for the required original MIT license.
"""
from __future__ import annotations


class ConversationManager:
    """Maintains rolling conversation history for a single session/request."""

    def __init__(self, max_turns: int = 20, system_prompt: str = "", instruction_prompt: str = "") -> None:
        self.max_turns = max_turns
        combined_prompt = f"{system_prompt}\n\n[INSTRUCTIONS]\n{instruction_prompt}"
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": combined_prompt},
        ]

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str, tool_calls: list[dict] | None = None) -> None:
        message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        self.messages.append(message)
        self._trim()

    def add_tool_response(self, tool_call_id: str, name: str, content: str) -> None:
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
        })
        self._trim()

    def get_messages(self) -> list[dict[str, str]]:
        return list(self.messages)

    def _trim(self) -> None:
        """Keep system prompt + last max_turns pairs."""
        system = self.messages[0]
        conversation = self.messages[1:]
        max_msgs = self.max_turns * 2
        if len(conversation) > max_msgs:
            self.messages = [system] + conversation[-max_msgs:]
