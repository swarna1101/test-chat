import google.generativeai as genai
import structlog

from flare_ai_social.settings import settings

logger = structlog.get_logger(__name__)
genai.configure(api_key=settings.gemini_api_key)


def start() -> None:
    tuned_model_id = settings.tuned_model_name
    tuned_models = [m.name for m in genai.list_tuned_models()]
    logger.info("available tuned models", tuned_models=tuned_models)

    model_info = genai.get_tuned_model(name=f"tunedModels/{tuned_model_id}")
    logger.info("tuned model info", model_info=model_info)

    model = genai.GenerativeModel(model_name=f"tunedModels/{tuned_model_id}")

    prompts = [
        "Uhhh, sorry guys, did we forget we are building the tech for the future?",
        "Already have yield on my XRP.",
    ]
    for prompt in prompts:
        result = model.generate_content(prompt)
        logger.info("generate", prompt=prompt, result=result.text)

    # To be done:
    # - X API integration
    # - X reply and notification handling logic


if __name__ == "__main__":
    start()
