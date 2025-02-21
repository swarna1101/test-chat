# 🤖 Flare AI Social

A robust, extensible social media bot framework that monitors and automatically responds to mentions across multiple platforms using AI-powered responses.

## 🚀 Key Features

- **Multi-platform Support**: Monitor mentions and messages across Twitter/X and Telegram
- **AI-powered Responses**: Generate contextually relevant replies using Google's Gemini AI
- **Model Fine-tuning**: Support for custom-tuned models with example dataset
- **Rate Limit Handling**: Built-in exponential backoff and retry mechanisms
- **TEE Integration**: Secure execution in Trusted Execution Environment

## 🏗️ Project Structure

```
src/flare_ai_social/
├── ai/                     # AI Provider implementations
│   ├── base.py            # Base AI provider abstraction
│   ├── gemini.py          # Google Gemini integration
│   └── openrouter.py      # OpenRouter integration
├── api/                    # API layer
│   └── routes/            # API endpoint definitions
├── attestation/           # TEE attestation implementation
│   ├── vtpm_attestation.py # vTPM client
│   └── vtpm_validation.py  # Token validation
├── prompts/               # Prompt engineering templates
│   └── templates.py       # Different prompt strategies
├── telegram/              # Telegram bot implementation
│   └── service.py         # Telegram service logic
├── twitter/               # Twitter bot implementation
│   └── service.py         # Twitter service logic
├── bot_manager.py         # Bot orchestration
├── main.py                # FastAPI application
├── settings.py            # Configuration settings
└── tune_model.py          # Model fine-tuning utilities
```

## 🏗️ Build & Run Instructions

### Fine-tuning a Model

1. **Prepare Environment File**:  
   Rename `.env.example` to `.env` and update these model fine-tuning parameters:

   | Parameter             | Description                                                                | Default                              |
      | --------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
   | `tuned_model_name`    | Name of the newly tuned model.                                             | `pugo-hilion`                        |
   | `tuning_source_model` | Name of the foundational model to tune on.                                 | `models/gemini-1.5-flash-001-tuning` |
   | `epoch_count`         | Number of tuning epochs to run. An epoch is a pass over the whole dataset. | `30`                                 |
   | `batch_size`          | Number of examples to use in each training batch.                          | `4`                                  |
   | `learning_rate`       | Step size multiplier for the gradient updates.                             | `0.001`                              |

2. **Prepare Dataset**:
   - Example dataset provided in `src/data/training_data.json`
   - Based on Hugo Philion's X/Twitter feed
   - Compatible with any public dataset

3. **Tune Model**:
   ```bash
   uv run start-tuning
   ```

4. **Observe loss parameters:**
   After tuning in complete, a training loss PNG will be saved in the root folder corresponding to the new model.
   Ideally the loss should minimize to near 0 after several training epochs.

![pugo-hilion_mean_loss](https://github.com/user-attachments/assets/f6c4d82b-678a-4ae5-bfb7-39dc59e1103d)

5. **Test Model**:
   Select the new tuned model and compare it against a set of prompting techniques (zero-shot, few-shot and chain-of-thought):

   ```bash
   uv run start-compare
   ```
   
### Running Social Bots

1. **Configure Platforms:**
  - Set up Twitter/X API credentials 
  - Configure Telegram bot token 
  - Enable/disable platforms as needed

2. **Start Bots:**

   ```bash
   uv run start-bots
   ```
   
### Build with Docker

After model training:

1. **Build Image**:
   ```bash
   docker build -t flare-ai-social .
   ```

2. **Run Container**:
   ```bash
   docker run -p 80:80 -it --env-file .env flare-ai-social
   ```

3. **Access UI**: Navigate to `http://localhost:80`

## 🚀 Deploy on TEE

Deploy on Confidential Space Instance (AMD SEV/Intel TDX) for hardware-backed security.

### Prerequisites

- GCP account with `verifiable-ai-hackathon` access
- [Gemini API key](https://aistudio.google.com/app/apikey)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed

### Environment Setup

1. **Configure Environment**:
   ```bash
   # In .env file
   TEE_IMAGE_REFERENCE=ghcr.io/flare-foundation/flare-ai-social:main
   INSTANCE_NAME=<PROJECT_NAME-TEAM_NAME>
   ```

2. **Load Variables**:
   ```bash
   source .env
   ```

### Deployment

Deploy to Confidential Space (AMD SEV):

```bash
gcloud compute instances create $INSTANCE_NAME \
  --project=verifiable-ai-hackathon \
  --zone=us-central1-c \
  --machine-type=n2d-standard-2 \
  --network-interface=network-tier=PREMIUM,nic-type=GVNIC,stack-type=IPV4_ONLY,subnet=default \
  --metadata=tee-image-reference=$TEE_IMAGE_REFERENCE,\
tee-container-log-redirect=true,\
tee-env-GEMINI_API_KEY=$GEMINI_API_KEY,\
tee-env-GEMINI_MODEL=$GEMINI_MODEL,\
tee-env-WEB3_PROVIDER_URL=$WEB3_PROVIDER_URL,\
tee-env-SIMULATE_ATTESTATION=false \
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

### Post-deployment

Monitor startup in [GCP Console](https://console.cloud.google.com/welcome?project=verifiable-ai-hackathon) under **Serial port 1**. When you see:

```plaintext
INFO: Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

Access the UI via the instance's external IP.

## 💡 Example Use Cases & Next Steps

TODO: Add example use cases and next steps for the project.