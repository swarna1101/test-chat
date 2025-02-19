import google.generativeai as genai
import structlog

from flare_ai_social.ai import GeminiProvider
from flare_ai_social.prompts import (
    CHAIN_OF_THOUGHT_PROMPT,
    FEW_SHOT_PROMPT,
    ZERO_SHOT_PROMPT,
)
from flare_ai_social.settings import settings

logger = structlog.get_logger(__name__)
genai.configure(api_key=settings.gemini_api_key)

# Test prompts are selected from within the training dataset
# The first prompt is general and conversational
# The second prompt is confusing without any context
TEST_PROMPTS = [
    "Uhhh, sorry guys, did we forget we are building the tech for the future?",
    "Already have yield on my XRP.",
]


def test_prompts(model: GeminiProvider, label: str) -> None:
    for prompt in TEST_PROMPTS:
        result = model.generate(prompt)
        logger.info(label, prompt=prompt, result=result.text)


def start() -> None:
    tuned_model_id = settings.tuned_model_name
    tuned_models = [m.name for m in genai.list_tuned_models()]
    logger.info("available tuned models", tuned_models=tuned_models)

    model_info = genai.get_tuned_model(name=f"tunedModels/{tuned_model_id}")
    logger.info("tuned model info", model_info=model_info)

    tuned_model = genai.GenerativeModel(model_name=f"tunedModels/{tuned_model_id}")
    # Test tuned model
    for prompt in TEST_PROMPTS:
        result = tuned_model.generate_content(prompt)
        logger.info("tuned_model", prompt=prompt, result=result.text)

    # Compare with zero-shot prompt
    model_zero_shot = GeminiProvider(
        settings.gemini_api_key,
        model="gemini-1.5-flash",
        system_instruction=ZERO_SHOT_PROMPT,
    )
    test_prompts(model=model_zero_shot, label="zero-shot")

    # Compare with few-shot prompt
    model_few_shot = GeminiProvider(
        settings.gemini_api_key,
        model="gemini-1.5-flash",
        system_instruction=FEW_SHOT_PROMPT,
    )
    test_prompts(model=model_few_shot, label="few-shot")

    # Compare with chain-of-thought prompt
    model_chain_of_thought = GeminiProvider(
        settings.gemini_api_key,
        model="gemini-1.5-flash",
        system_instruction=CHAIN_OF_THOUGHT_PROMPT,
    )
    test_prompts(model=model_chain_of_thought, label="chain-of-thought")

    # To be done:
    # - X API integration
    # - X reply and notification handling logic


if __name__ == "__main__":
    start()
