# Flare AI Social

A robust, extensible social media bot framework that monitors and automatically responds to mentions across multiple platforms using AI-powered responses.

## Overview

Flare AI Social is a Python-based system that connects AI capabilities with social media platforms. The bot monitors designated accounts for mentions, processes them using AI, and automatically responds with contextually appropriate replies.

Currently supported platforms:

- Twitter/X
- Telegram

## Features

- **Multi-platform monitoring**: Monitor mentions/keywords across Twitter and messages in Telegram
- **AI-powered responses**: Generate contextually relevant replies using Google's Gemini AI
- **Rate limit handling**: Built-in exponential backoff and retry mechanisms
- **Model customization**: Support for custom-tuned AI models

## Architecture

The system consists of three main components:

1. **Bot Manager**: Coordinates all bots and handles initialization, monitoring, and shutdown
2. **Platform-specific Bots**: Implementations for Twitter and Telegram
3. **AI Provider**: Interface to the AI model (currently supports Google Gemini)

## Prerequisites

- Python 3.12+
- Google Gemini API key
- Twitter/X API credentials (API key, secret, access token, etc.)
- RapidAPI key for Twitter search functionality
- Telegram Bot API token (if using Telegram)

## Installation

```bash
# Clone the repository
git clone repo_url

# Install dependencies uv sync --all-extras
uv sync --all-extras

# Create .env file
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

Configure the bot by editing the `.env` file or setting environment variables:

```
# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key
TUNED_MODEL_NAME=pugo-hilion

# Twitter/X Bot Settings
ENABLE_TWITTER=true
X_API_KEY=your_twitter_api_key
X_API_KEY_SECRET=your_twitter_api_secret
X_ACCESS_TOKEN=your_twitter_access_token
X_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
RAPIDAPI_KEY=your_rapidapi_key
RAPIDAPI_HOST=twitter241.p.rapidapi.com
TWITTER_ACCOUNTS_TO_MONITOR=@YourAccount,@AnotherAccount,keyword
TWITTER_POLLING_INTERVAL=60

# Telegram Bot Settings
ENABLE_TELEGRAM=true
TELEGRAM_API_TOKEN=your_telegram_bot_token
TELEGRAM_ALLOWED_USERS= # empty to allow all accounts to interact with the bot
TELEGRAM_POLLING_INTERVAL=5

# Fine-tuning Parameters
TUNING_SOURCE_MODEL=models/gemini-1.5-flash-001-tuning
TUNING_EPOCH_COUNT=100
TUNING_BATCH_SIZE=4
TUNING_LEARNING_RATE=0.001
```

## 🏗️ Build & Run Instructions

### Running the Social Media Bots

Start the bots with UV:

```bash
uv run start-bots
```

### Fine-tuning a Model Over a Dataset

1. **Prepare the Environment File:**  
   Rename `.env.example` to `.env` and update the variables accordingly.
   Some parameters are specific to model fine-tuning:

   | Parameter             | Description                                                                | Default                              |
      | --------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
   | `tuned_model_name`    | Name of the newly tuned model.                                             | `pugo-hilion`                        |
   | `tuning_source_model` | Name of the foundational model to tune on.                                 | `models/gemini-1.5-flash-001-tuning` |
   | `epoch_count`         | Number of tuning epochs to run. An epoch is a pass over the whole dataset. | `100`                                |
   | `batch_size`          | Number of examples to use in each training batch.                          | `4`                                  |
   | `learning_rate`       | Step size multiplier for the gradient updates.                             | `0.001`                              |

2. **Prepare a dataset:**
   An example dataset is provided in `src/data/training_data.json`, which consists of tweet from
   [Hugo Philion's X](https://x.com/HugoPhilion) account. You can use any publicly available dataset
   for model fine-tuning.

3. **Tune a new model**
   Set the name of the new tuned model in `src/flare_ai_social/tune_model.py`, then:

   ```bash
   uv run start-tuning
   ```

4. **Observe loss parameters:**
   After tuning in complete, a training loss PNG will be saved in the root folder corresponding to the new model.
   Ideally the loss should minimize to near 0 after several training epochs.

5. **Test the new model**
   Select the new tuned model and test it against a set of prompts:

   ```bash
   uv run start-social
   ```

## Twitter/X Bot

The Twitter bot:

1. Monitors mentions of specified accounts using the RapidAPI Twitter search endpoint
2. Processes mentions to identify ones within the configured time window
3. Generates AI responses for valid mentions
4. Replies to mentions with the generated content

### Rate Limits

The Twitter component implements strategies to handle rate limits:

- Exponential backoff for retries
- Sequential (rather than concurrent) account monitoring
- Configurable polling intervals
- Comprehensive error handling

## Telegram Bot

The Telegram bot:

1. Listens for incoming messages
2. Optionally filters messages based on allowed user IDs
3. Processes messages through the AI provider
4. Replies with generated responses

## AI Provider

The system uses Google's Gemini AI models with:

- Support for default models (gemini-1.5-flash)
- Optional integration with custom-tuned models
- Fallback mechanisms if tuned models are unavailable
- Configurable system prompts for controlling AI behavior

## Extending the System

### Adding New Social Platforms

To add a new platform:

1. Create a new class that implements the platform's API
2. Follow the pattern established by `TwitterBot` and `TelegramBot`
3. Add the new bot to `BotManager`

### Using Different AI Models

The system uses a provider pattern for AI integration:

1. Create a new class that implements the `BaseAIProvider` interface
2. Implement the `generate` method to interface with your AI service
3. Configure the `BotManager` to use your provider

## Troubleshooting

### Twitter Rate Limits

- Increase `TWITTER_POLLING_INTERVAL` to reduce API calls
- Reduce the number of monitored accounts
- Upgrade your RapidAPI plan for higher limits

### Connection Timeouts

- Check network connectivity
- Verify API credentials
- Ensure clock synchronization for OAuth
- Monitor Twitter API status
