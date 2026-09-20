from langsmith.integrations.otel import OtelSpanProcessor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from dotenv import load_dotenv

def setup_tracing():
    """Function that is used to trace agent"""

    # loading environment variables
    load_dotenv()

    # Configuring langsmith otel tracer
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    provider.add_span_processor(OtelSpanProcessor())

    # To trace Agent or task delegations in Crewai
    CrewAIInstrumentor().instrument(tracer_provider = provider)
    # To trace underlying llm calls made via litellm
    LiteLLMInstrumentor().instrument(tracer_provider = provider)