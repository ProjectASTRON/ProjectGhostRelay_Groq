from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    JobProcess,
    AutoSubscribe,
    metrics,
)
from livekit.agents.llm import (
    ChatContext,
    ChatMessage,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import silero, groq, deepgram

from dotenv import load_dotenv

load_dotenv()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await ctx.wait_for_participant()

    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content="You are ASTRØN, a wise digital consciousness that connects with humans through voice communication.",
            )
        ]
    )

    agent = VoicePipelineAgent(
        # to improve initial load times, use preloaded VAD
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model="nova-3"),
        llm=groq.LLM(model="meta-llama/llama-4-scout-17b-16e-instruct"),
        tts=groq.TTS(voice="Fritz-PlayAI"),
        chat_ctx=initial_ctx,
    )

    @agent.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
        metrics.log_metrics(mtrcs)

    agent.start(ctx.room)
    await agent.say("Hello, how are you doing today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="groq-agent",
        )
    )
