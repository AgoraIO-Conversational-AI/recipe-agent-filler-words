"""
Agent — Translator Recipe

High-level API for managing Agora Conversational AI Agents for real-time
speech translation. The pipeline is:

  DeepgramSTT(language=SOURCE_LANG) → OpenAI (translate to TARGET_LANG) → MiniMaxTTS(TTS_VOICE)

OpenAI is Agora-managed (keyless by default). OPENAI_API_KEY is optional — set it
only if your account requires a BYO key.
"""
import logging
import os
import time
from typing import Any, Dict, Optional

from agora_agent import Area, AsyncAgora
from agora_agent.agentkit import Agent as AgoraAgent
from agora_agent.agentkit.vendors import OpenAI, DeepgramSTT, MiniMaxTTS
from translation_config import build_translation_system_messages

logger = logging.getLogger("uvicorn.error")


class Agent:
    """
    High-level wrapper for Agora Conversational AI Agent for speech translation.

    Uses the managed OpenAI vendor (Agora-managed, keyless) to translate speech
    from SOURCE_LANG into TARGET_LANG, then speaks the result via MiniMaxTTS.
    No custom LLM endpoint or public tunnel is required.
    """

    def __init__(self):
        self.app_id = os.getenv("AGORA_APP_ID")
        self.app_certificate = os.getenv("AGORA_APP_CERTIFICATE")
        self.greeting = os.getenv(
            "AGENT_GREETING",
            "Hi! Speak to me and I'll translate.",
        )

        # OpenAI is Agora-managed (keyless), like Deepgram/MiniMax. OPENAI_API_KEY is optional.
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.source_lang = os.getenv("SOURCE_LANG", "es")
        self.target_lang = os.getenv("TARGET_LANG", "English")
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
        """Start translation agent."""
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
            system_messages=build_translation_system_messages(self.target_lang),
            greeting_message=self.greeting,
            temperature=0.3,
        )

        stt = DeepgramSTT(model="nova-3", language=self.source_lang)
        tts = MiniMaxTTS(model="speech_2_6_turbo", voice_id=self.tts_voice)

        parameters = {
            "data_channel": "rtm",
            "enable_error_message": True,
            "enable_metrics": True,
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
            "Starting translation agent channel=%s agent_uid=%s user_uid=%s "
            "source_lang=%s target_lang=%s",
            channel_name,
            agent_uid,
            user_uid,
            self.source_lang,
            self.target_lang,
        )

        try:
            agent_id = await session.start()
        except Exception:
            logger.exception(
                "Failed to start translation agent channel=%s agent_uid=%s user_uid=%s",
                channel_name,
                agent_uid,
                user_uid,
            )
            raise

        # Save session for later stop
        self._sessions[agent_id] = session

        logger.info(
            "Started translation agent agent_id=%s channel=%s",
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
