import google.generativeai as genai
import structlog

from flare_ai_social.settings import settings

logger = structlog.get_logger(__name__)
genai.configure(api_key=settings.gemini_api_key)


def start(tuned_model_id: str) -> None:
    tuned_model_id = "pugo-hillion"

    tuned_models = [m.name for m in genai.list_tuned_models()]
    logger.info("available tuned models", tuned_models=tuned_models)

    model_info = genai.get_tuned_model(name=f"tunedModels/{tuned_model_id}")
    logger.info("tuned model info", model_info=model_info)

    model = genai.GenerativeModel(model_name=f"tunedModels/{tuned_model_id}")
    prompt = "Uhhh, sorry guys, did we forget we are building the tech for the future?"
    result = model.generate_content(prompt)
    logger.info("generate", prompt=prompt, result=result.text)

    # To be done:
    # - X API integration
    # - X reply and notification handling logic


if __name__ == "__main__":
    start(tuned_model_id="pugo-hillion")
