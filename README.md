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
| `epoch_count`         | Number of tuning epochs to run. An epoch is a pass over the whole dataset. | `30`                                 |
| `batch_size`          | Number of examples to use in each training batch.                          | `4`                                  |
| `learning_rate`       | Step size multiplier for the gradient updates.                             | `0.001`                              |

### Fine tuning a model over a dataset

1. **Prepare a dataset:**
   An example dataset is provided in `src/data/training_data.json`, which consists of tweets from
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

   ![pugo-hilion_mean_loss](https://github.com/user-attachments/assets/f6c4d82b-678a-4ae5-bfb7-39dc59e1103d)

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

## 🚀 Deploy on TEE

Deploy on a [Confidential Space](https://cloud.google.com/confidential-computing/confidential-space/docs/confidential-space-overview) using AMD SEV.

### Prerequisites

- **Google Cloud Platform Account:**  
  Access to the [`verifiable-ai-hackathon`](https://console.cloud.google.com/welcome?project=verifiable-ai-hackathon) project is required.

- **Gemini API Key:**  
  Ensure your [Gemini API key](https://aistudio.google.com/app/apikey) is linked to the project.

- **gcloud CLI:**  
  Install and authenticate the [gcloud CLI](https://cloud.google.com/sdk/docs/install).

### Environment Configuration

1. **Set Environment Variables:**  
   Update your `.env` file with:

   ```bash
   TEE_IMAGE_REFERENCE=ghcr.io/flare-foundation/flare-ai-social:main  # Replace with your repo build image
   INSTANCE_NAME=<PROJECT_NAME-TEAM_NAME>
   ```

2. **Load Environment Variables:**

   ```bash
   source .env
   ```

   > **Reminder:** Run the above command in every new shell session.

3. **Verify the Setup:**

   ```bash
   echo $TEE_IMAGE_REFERENCE # Expected output: Your repo build image
   ```

### Deploying to Confidential Space

Run the following command:

```bash
gcloud compute instances create $INSTANCE_NAME \
  --project=verifiable-ai-hackathon \
  --zone=us-central1-a \
  --machine-type=n2d-standard-2 \
  --network-interface=network-tier=PREMIUM,nic-type=GVNIC,stack-type=IPV4_ONLY,subnet=default \
  --metadata=tee-image-reference=$TEE_IMAGE_REFERENCE,\
tee-container-log-redirect=true,\
tee-env-GEMINI_API_KEY=$GEMINI_API_KEY,\
tee-env-TUNED_MODEL_NAME=$TUNED_MODEL_NAME,\
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account=confidential-sa@verifiable-ai-hackathon.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --min-cpu-platform="AMD Milan" \
  --tags=flare-ai,http-server,https-server \
  --create-disk=auto-delete=yes,\
boot=yes,\
device-name=$INSTANCE_NAME,\
image=projects/confidential-space-images/global/images/confidential-space-debug-250100,\
mode=rw,\
size=11,\
type=pd-standard \
  --shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --reservation-affinity=any \
  --confidential-compute-type=SEV
```

#### Post-deployment

After deployment, you should see an output similar to:

```plaintext
NAME          ZONE           MACHINE_TYPE    PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP    STATUS
social-team1   us-central1-a  n2d-standard-2               10.128.0.18  34.41.127.200  RUNNING
```

It may take a few minutes for Confidential Space to complete startup checks.
You can monitor progress via the [GCP Console](https://console.cloud.google.com/welcome?project=verifiable-ai-hackathon) by clicking **Serial port 1 (console)**.
When you see a message like:

```plaintext
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

the container is ready. Navigate to the external IP of the instance (visible in the GCP Console) to access the Chat UI.

### 🔧 Troubleshooting

If you encounter issues, follow these steps:

1. **Check Logs:**

   ```bash
   gcloud compute instances get-serial-port-output $INSTANCE_NAME --project=verifiable-ai-hackathon
   ```

2. **Verify API Key(s):**  
   Ensure that all API Keys are set correctly (e.g. `GEMINI_API_KEY`).

3. **Check Firewall Settings:**  
   Confirm that your instance is publicly accessible on port `80`.
