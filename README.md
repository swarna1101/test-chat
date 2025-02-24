# Flare AI Social

Flare AI Kit template for Social AI Agents.

## 🚀 Key Features

- **Secure AI Execution**  
  Runs within a Trusted Execution Environment (TEE) featuring remote attestation support for robust security.

- **Built-in Chat UI**  
  Interact with your AI via a TEE-served chat interface.

- **Gemini Fine-Tuning Support**  
  Fine-tune foundational models with custom datasets.

- **Social media integrations**  
  X and Telegram integrations with with rate limiting and retry mechanisms.

## 🎯 Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Fine-tune a model

1. **Prepare Environment File**: Rename `.env.example` to `.env` and update these model fine-tuning parameters:

   | Parameter             | Description                                                               | Default                            |
   | --------------------- | ------------------------------------------------------------------------- | ---------------------------------- |
   | `tuned_model_name`    | Name of the newly tuned model                                             | pugo-hilion                        |
   | `tuning_source_model` | Name of the foundational model to tune on                                 | models/gemini-1.5-flash-001-tuning |
   | `epoch_count`         | Number of tuning epochs to run. An epoch is a pass over the whole dataset | 30                                 |
   | `batch_size`          | Number of examples to use in each training batch                          | 4                                  |
   | `learning_rate`       | Step size multiplier for the gradient updates                             | 0.001                              |

2. **Prepare a dataset:**
   An example dataset is provided in `src/data/training_data.json`, which consists of tweets from
   [Hugo Philion's X](https://x.com/HugoPhilion) account. You can use any publicly available dataset
   for model fine-tuning.

3. **Tune a new model:**
   Depending on the size of your dataset, this process can take several minutes:

   ```bash
   uv run start-tuning
   ```

4. **Observe loss parameters:**
   After tuning in complete, a training loss PNG will be saved in the root folder corresponding to the new model.
   Ideally the loss should minimize to near 0 after several training epochs.

   ![pugo-hilion_mean_loss](https://github.com/user-attachments/assets/f6c4d82b-678a-4ae5-bfb7-39dc59e1103d)

5. **Test the new model:**
   Select the new tuned model and compare it against a set of prompting techniques (zero-shot, few-shot and chain-of-thought):

   ```bash
   uv run start-compare
   ```

6. **Start Social Bots (optional):**:

   - Set up Twitter/X API credentials
   - Configure Telegram bot token
   - Enable/disable platforms as needed

   ```bash
   uv run start-bots
   ```

### Build Using Docker (Recommended)

The Docker setup mimics a TEE environment and includes an Nginx server for routing, while Supervisor manages both the backend and frontend services in a single container.

1. **Build the Docker image**:

   ```bash
   docker build -t flare-ai-social .
   ```

2. **Run the Docker Container:**

   ```bash
   docker run -p 80:80 -it --env-file .env flare-ai-social
   ```

3. **Access the Frontend:**  
   Open your browser and navigate to [http://localhost:80](http://localhost:80) to interact with the tuned model via the Chat UI.

### 🛠 Build Manually

Flare AI Social is composed of a Python-based backend and a JavaScript frontend. Follow these steps for manual setup:

#### Backend Setup

1. **Install Dependencies:**
   Use [uv](https://docs.astral.sh/uv/getting-started/installation/) to install backend dependencies:

   ```bash
   uv sync --all-extras
   ```
   
2. **Start the Backend:**
   The backend runs by default on `0.0.0.0:80`:

    ```bash
   uv run start-backend
    ```

#### Frontend Setup

1. **Install Dependencies:**
   In the `chat-ui/` directory, install the required packages using [npm](https://nodejs.org/en/download):

   ```bash
   cd chat-ui/
   npm install
   ```

2. **Configure the Frontend:**
   Update the backend URL in `chat-ui/src/App.js` for testing:

   ```js
   const BACKEND_ROUTE = "http://localhost:8080/api/routes/chat/";
   ```

   > **Note:** Remember to change `BACKEND_ROUTE` back to `'api/routes/chat/'` after testing.

3. **Start the Frontend:**

   ```bash
   npm start
   ```
   
## 📁 Repo Structure

```plaintext
src/flare_ai_social/
├── ai/                            # AI Provider implementations
│   ├── base.py                    # Base AI provider abstraction
│   ├── gemini.py                  # Google Gemini integration
│   └── openrouter.py             # OpenRouter integration
├── api/                           # API layer
│   └── routes/                    # API endpoint definitions
├── attestation/                   # TEE attestation implementation
│   ├── vtpm_attestation.py       # vTPM client
│   └── vtpm_validation.py        # Token validation
├── prompts/                       # Prompt engineering templates
│   └── templates.py              # Different prompt strategies
├── telegram/                      # Telegram bot implementation
│   └── service.py                # Telegram service logic
├── twitter/                       # Twitter bot implementation
│   └── service.py                # Twitter service logic
├── bot_manager.py                # Bot orchestration
├── main.py                       # FastAPI application
├── settings.py                   # Configuration settings
└── tune_model.py                 # Model fine-tuning utilities
```

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

## 💡 Next Steps

TODO
