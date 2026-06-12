"""
Agent — Filler Words Recipe

High-level API for managing Agora Conversational AI Agents with latency
smoothing and graceful exit. The pipeline is:

  DeepgramSTT(nova-3) → OpenAI (friendly assistant) → MiniMaxTTS

OpenAI is Agora-managed (keyless by default). OPENAI_API_KEY is optional — set
it only if your account requires a BYO key.

Features:
  - filler_words: static phrase list played during LLM latency gaps
  - farewell_config: graceful exit before the agent leaves on stop
"""
import logging
import os
import time
from typing import Any, Dict, Optional

from agora_agent import Area, AsyncAgora
from agora_agent.agentkit import Agent as AgoraAgent
from agora_agent.agentkit.vendors import OpenAI, DeepgramSTT, MiniMaxTTS
from filler_config import build_filler_words, build_farewell

logger = logging.getLogger("uvicorn.error")

AGENT_SYSTEM_PROMPT = (
    "You are a friendly, concise voice assistant. "
    "Keep replies to one or two sentences."
)


class Agent:
    """
    High-level wrapper for Agora Conversational AI Agent with filler-words and
    graceful-exit support.

    Uses the managed OpenAI vendor (Agora-managed, keyless) for conversation.
    Filler phrases are played during LLM latency so the experience feels natural.
    A farewell_config ensures the agent says goodbye gracefully before stopping.
    No custom LLM endpoint or public tunnel is required.
    """

    def __init__(self):
        self.app_id = os.getenv("AGORA_APP_ID")
        self.app_certificate = os.getenv("AGORA_APP_CERTIFICATE")
        self.greeting = os.getenv(
            "AGENT_GREETING",
            "Hi! Ask me anything — you'll hear me think out loud while I work.",
        )

        # OpenAI is Agora-managed (keyless), like Deepgram/MiniMax. OPENAI_API_KEY is optional.
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.tts_voice = os.getenv("TTS_VOICE", "English_captivating_female1")

        if not self.app_id or not self.app_certificate:
            raise ValueError("AGORA_APP_ID and AGORA_APP_CERTIFICATE are required")

        self.client = AsyncAgora(
            area=Area.US,
            app_id=self.app_id,
            app_certificate=self.app_certificate,
        )

        # Track active sessions by agent_id
        self._sessions: Dict[str, Any] = {}

    async def start(
        self,
        channel_name: str,
        agent_uid: int,
        user_uid: int,
        output_audio_codec: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start filler-words agent."""
        if not channel_name or not str(channel_name).strip():
            raise ValueError("channel_name is required and cannot be empty")
        if agent_uid <= 0:
            raise ValueError("agent_uid is required and cannot be empty")
        if user_uid <= 0:
            raise ValueError("user_uid is required and cannot be empty")

        name = f"agent_{channel_name}_{agent_uid}_{int(time.time())}"

        llm = OpenAI(
            api_key=self.openai_api_key,
            model=self.openai_model,
            system_messages=[{"role": "system", "content": AGENT_SYSTEM_PROMPT}],
            greeting_message=self.greeting,
            temperature=0.7,
        )

        stt = DeepgramSTT(model="nova-3")
        tts = MiniMaxTTS(model="speech_2_6_turbo", voice_id=self.tts_voice)

        parameters = {
            "data_channel": "rtm",
            "enable_error_message": True,
            "enable_metrics": True,
            "farewell_config": build_farewell(),
        }
        if isinstance(output_audio_codec, str) and output_audio_codec.strip():
            parameters["output_audio_codec"] = output_audio_codec.strip()

        agora_agent = AgoraAgent(
            name=name,
            greeting=self.greeting,
            failure_message="Please wait a moment.",
            max_history=50,
            turn_detection={
                "config": {
                    "speech_threshold": 0.5,
                    "start_of_speech": {
                        "mode": "vad",
                        "vad_config": {
                            "interrupt_duration_ms": 160,
                            "prefix_padding_ms": 300,
                        },
                    },
                    "end_of_speech": {
                        "mode": "vad",
                        "vad_config": {
                            "silence_duration_ms": 480,
                        },
                    },
                },
            },
            advanced_features={"enable_rtm": True},
            parameters=parameters,
            filler_words=build_filler_words(),
        )

        agora_agent = (
            agora_agent
            .with_stt(stt)
            .with_llm(llm)
            .with_tts(tts)
        )

        session = agora_agent.create_async_session(
            client=self.client,
            channel=channel_name,
            agent_uid=str(agent_uid),
            remote_uids=[str(user_uid)],
            enable_string_uid=False,
            idle_timeout=30,
            expires_in=3600,
        )

        logger.info(
            "Starting filler-words agent channel=%s agent_uid=%s user_uid=%s",
            channel_name,
            agent_uid,
            user_uid,
        )

        try:
            agent_id = await session.start()
        except Exception:
            logger.exception(
                "Failed to start filler-words agent channel=%s agent_uid=%s user_uid=%s",
                channel_name,
                agent_uid,
                user_uid,
            )
            raise

        # Save session for later stop
        self._sessions[agent_id] = session

        logger.info(
            "Started filler-words agent agent_id=%s channel=%s",
            agent_id,
            channel_name,
        )

        return {
            "agent_id": agent_id,
            "channel_name": channel_name,
            "status": "started",
        }

    async def stop(self, agent_id: str) -> None:
        """Stop a running agent. Falls back to the stateless client path."""
        if not agent_id or not str(agent_id).strip():
            raise ValueError("agent_id is required and cannot be empty")

        session = self._sessions.pop(agent_id, None)
        if session:
            try:
                await session.stop()
                logger.info("Stopped agent from active session agent_id=%s", agent_id)
                return
            except Exception:
                logger.warning(
                    "Failed to stop agent from active session; falling back agent_id=%s",
                    agent_id,
                    exc_info=True,
                )

        logger.info("Stopping agent through client.stop_agent agent_id=%s", agent_id)
        await self.client.stop_agent(agent_id)
