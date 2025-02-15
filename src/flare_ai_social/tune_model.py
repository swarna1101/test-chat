import google.generativeai as genai
import pandas as pd
import seaborn as sns
import structlog

from flare_ai_social.prompts import training_dataset
from flare_ai_social.settings import settings

logger = structlog.get_logger(__name__)
genai.configure(api_key=settings.gemini_api_key)


def list_models_supporting_tuning() -> None:
    models = [m.name for m in genai.list_models() if "createTunedModel" in m.supported_generation_methods]
    logger.info("models supporting tuning supported", models=models)


def start(new_model_id: str) -> None:
    # Check if model exists and delete it
    for tuned_model in genai.list_tuned_models():
        if tuned_model.name == f"tunedModels/{new_model_id}":
            logger.info("deleting existing model", tuned_model_id=new_model_id)
            genai.delete_tuned_model(f"tunedModels/{new_model_id}")

    # Create tuning operation
    operation = genai.create_tuned_model(
        id=new_model_id,
        source_model="models/gemini-1.5-flash-001-tuning",
        training_data=training_dataset,
        epoch_count=50,
        batch_size=4,
        learning_rate=0.005,
    )

    # Wait for tuning to finish
    logger.info("tuning model (takes a few mins)", tuned_model_id=new_model_id)
    for _status in operation.wait_bar():
        pass
    tuned_model = operation.result()
    logger.info("tuning complete", tuned_model=tuned_model)

    # Save mean loss to figure
    snapshots = pd.DataFrame(tuned_model.tuning_task.snapshots)
    plot = sns.lineplot(data=snapshots, x="epoch", y="mean_loss")
    plot.set_title(new_model_id)
    save_fig_path = f"{new_model_id}_mean_loss.png"
    plot.get_figure().savefig(save_fig_path)  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]
    logger.info("saved mean_loss", save_fig_path=save_fig_path)


if __name__ == "__main__":
    list_models_supporting_tuning()
    # start("pugo-hillion")
