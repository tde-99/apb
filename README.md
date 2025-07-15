# Autoposter Bot

## About

Autoposter Bot is a Telegram bot that allows you to automatically forward messages from one or more source channels to a target channel. It is highly configurable and provides a variety of features to customize the forwarding process.

## Features

- **Job-Based Forwarding:** Create and manage multiple forwarding jobs.
- **Customizable Forwarding:**
    - Set a range of messages to forward.
    - Configure the batch size and recurring time for forwarding.
    - Set a timer to automatically delete forwarded messages.
- **Filtering:** Filter messages by type (media, text, or all).
- **Custom Captions and Buttons:** Add custom captions and inline buttons to forwarded messages.
- **User Management:** The bot manages user states and interactions.
- **Admin Statistics:** Admins can view usage statistics.
- **Force Subscription:** Require users to subscribe to a channel before using the bot.
- **Edit and Cancel Jobs:** Easily edit or delete existing forwarding jobs.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/autoposter-bot.git
   cd autoposter-bot
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

You can configure the bot using environment variables or by editing the `config.py` file. It is recommended to use environment variables for sensitive information like API credentials and bot tokens.

### Using Environment Variables

Create a `.env` file in the root of the project and add the following variables:

```
API_ID="your_api_id"
API_HASH="your_api_hash"
BOT_TOKEN="your_bot_token"
MONGO_URI="your_mongodb_uri"
MONGO_DB_NAME="your_mongodb_database_name"
FORCE_SUB_CHANNEL_ID="@your_channel_username" # Optional
ADMIN_IDS="your_admin_id,another_admin_id" # Optional
```

### Using `config.py`

You can also set the configuration variables directly in the `config.py` file.

## Running the Bot

To run the bot, simply execute the following command:

```bash
python bot.py
```
