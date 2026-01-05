"""Slack bot for translation service."""
import os
import logging
from typing import Dict, Any

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)


def translate_text(text: str) -> Dict[str, Any]:
    """
    Call backend API to translate text.
    
    Args:
        text: Text to translate
        
    Returns:
        Translation result dictionary
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/translate",
            json={"text": text},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return {"error": error_detail}
    
    except requests.Timeout:
        return {"error": "Translation request timed out"}
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return {"error": str(e)}


def format_translation_blocks(result: Dict[str, Any]) -> list:
    """
    Format translation result as Slack Block Kit.
    
    Args:
        result: Translation result dictionary
        
    Returns:
        List of Slack blocks
    """
    if "error" in result:
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"❌ *Translation failed:* {result['error']}"
                }
            }
        ]
    
    language_name = "English" if result["detected_language"] == "en" else "Korean"
    quality = result["quality_score"]
    
    # Quality indicator
    if quality >= 0.7:
        quality_emoji = "✅"
        quality_text = "High quality"
    elif quality >= 0.5:
        quality_emoji = "⚠️"
        quality_text = "Moderate quality"
    else:
        quality_emoji = "❌"
        quality_text = "Low quality"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Translation Result"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Detected Language:*\n{language_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Quality Score:*\n{quality:.2f} {quality_emoji} {quality_text}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Original:*\n{result['original']}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Translation:*\n{result['translation']}"
            }
        }
    ]
    
    return blocks


@app.command("/translate")
def handle_translate_command(ack, command, say):
    """
    Handle /translate slash command.
    
    Args:
        ack: Acknowledgement function
        command: Command payload
        say: Say function to send messages
    """
    ack()
    
    text = command.get("text", "").strip()
    
    if not text:
        say("Please provide text to translate. Usage: `/translate [text]`")
        return
    
    # Show processing message
    say("Translating... ⏳")
    
    # Translate
    result = translate_text(text)
    blocks = format_translation_blocks(result)
    
    # Send result in thread
    say(blocks=blocks, thread_ts=command.get("thread_ts"))


@app.event("app_mention")
def handle_mention(event, say):
    """
    Handle bot mentions.
    
    Args:
        event: Event payload
        say: Say function to send messages
    """
    text = event.get("text", "")
    
    # Remove bot mention from text
    import re
    text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    
    if not text:
        say(
            "Hi! Mention me with text to translate. Example: `@translator Hello, world!`",
            thread_ts=event.get("ts")
        )
        return
    
    # Translate
    result = translate_text(text)
    blocks = format_translation_blocks(result)
    
    # Send result in thread
    say(blocks=blocks, thread_ts=event.get("ts"))


@app.event("message")
def handle_message_events(body, logger):
    """
    Handle message events (no-op to prevent warnings).
    
    Args:
        body: Event body
        logger: Logger instance
    """
    pass


def main():
    """Run the Slack bot."""
    if not SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN not set")
        return
    
    # Socket mode requires app-level token
    if SLACK_APP_TOKEN:
        logger.info("Starting Slack bot in Socket Mode...")
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
    else:
        logger.warning("SLACK_APP_TOKEN not set. Socket mode not available.")
        logger.info("Starting Slack bot in HTTP mode...")
        app.start(port=int(os.getenv("PORT", 3000)))


if __name__ == "__main__":
    main()
