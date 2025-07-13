from temporalio import activity
from slackstyler import SlackStyler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
from pydantic import BaseModel
from config import settings

class PostToSlackInput(BaseModel):
    message: str
    channel_id: str
    thread_ts: str

def sanitize_message(message: str) -> str:
    """Remove HTML tags like <hr> and <br> from message."""
    return message.replace('<hr>', '---').replace('<br>', '\t')

@activity.defn
async def post_to_slack(args: PostToSlackInput) -> None:
    """Post a message to a Slack thread."""
    client = WebClient(token=settings.slack_bot_token)

    try:
        sanitized_message = sanitize_message(args.message)
        client.chat_postMessage(
            channel=args.channel_id,
            text=f"🧠 {SlackStyler().convert(sanitized_message)}",
            thread_ts=args.thread_ts
        )
    except SlackApiError as e:
        logging.error(f"Error posting to Slack: {e}")
        raise
