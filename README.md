# Flare AI Social

Flare AI Kit template for Social AI Agents.

## 🏗️ Build & Run Instructions

**Prepare the Environment File:**  
   Rename `.env.example` to `.env` and update the variables accordingly.
   Some parameters are specific to model fine-tuning:

   | Parameter             | Description                                                                | Default                              |
   | --------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
   | `tuned_model_name`    | Name of the newly tuned model.                                             | `pugo-hilion`                        |
   | `tuning_source_model` | Name of the foundational model to tune on.                                 | `models/gemini-1.5-flash-001-tuning` |
   | `epoch_count`         | Number of tuning epochs to run. An epoch is a pass over the whole dataset. | `100`                                |
   | `batch_size`          | Number of examples to use in each training batch.                          | `4`                                  |
   | `learning_rate`       | Step size multiplier for the gradient updates.                             | `0.001`                              |

### Fine tuning a model over a dataset

1. **Prepare a dataset:**
   An example dataset is provided in `src/data/training_data.json`, which consists of tweet from
   [Hugo Philion's X](https://x.com/HugoPhilion) account. You can use any publicly available dataset
   for model fine-tuning.

2. **Tune a new model**
   Set the name of the new tuned model in `src/flare_ai_social/tune_model.py`, then:

   ```bash
   uv run start-tuning
   ```

3. **Observe loss parameters:**
   After tuning in complete, a training loss PNG will be saved in the root folder corresponding to the new model.
   Ideally the loss should minimize to near 0 after several training epochs.

4. **Test the new model**
   Select the new tuned model and compare it against a set of prompting techniques (zero-shot, few-shot and chain-of-thought):

   ```bash
   uv run start-compare
   ```

### Build using Docker (Recommended)

**Note:** You can only perform this step once you have finishing training a new model.

The Docker setup mimics a TEE environment and includes an Nginx server for routing, while Supervisor manages both the backend and frontend services in a single container.

1. **Build the Docker Image:**

   ```bash
   docker build -t flare-ai-social .
   ```

2. **Run the Docker Container:**

   ```bash
   docker run -p 80:80 -it --env-file .env flare-ai-social
   ```

3. **Access the Frontend:**  
   Open your browser and navigate to [http://localhost:80](http://localhost:80) to interact with the Chat UI.
