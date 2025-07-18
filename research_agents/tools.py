import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from config import settings

# Set up logging
logger = logging.getLogger(__name__)

class GetChannelsRequest(BaseModel):
    include_archived: bool = Field(default=False, description="Whether to include archived channels in the results")

class SlackSearchRequest(BaseModel):
    query: str = Field(description="Search query string to find messages")
    channels: Optional[str] = Field(default=None, description="Comma-separated list of channel names to search in")
    sort: str = Field(default="timestamp", description="Sort order: 'timestamp' (chronological) or 'score' (relevance)")
    count: int = Field(default=40, description="Number of results to return (1-100)")
    start_time: Optional[str] = Field(default=None, description="ISO format start time filter")
    end_time: Optional[str] = Field(default=None, description="ISO format end time filter")

class SlackSearchResult(BaseModel):
    query: str = Field(description="The search query that was executed")
    total: int = Field(description="Total number of matching messages")
    matches: List[Dict[str, Any]] = Field(description="List of matching message objects")
    pagination: Optional[Dict[str, Any]] = Field(default=None, description="Pagination information from Slack API")
    has_more: bool = Field(default=False, description="Whether there are more results available")

class ThreadInput(BaseModel):
    thread_url: str = Field(description="Slack thread URL to retrieve messages from")

class GetUserNameRequest(BaseModel):
    user_id: str = Field(description="Slack user ID to get the display name for")

@activity.defn
def get_slack_channels(request: GetChannelsRequest) -> List[Dict[str, Any]]:
    try:
        client = get_slack_client()
        channel_types = ["public_channel"]
        response = client.conversations_list(
            exclude_archived=not request.include_archived,
            types=",".join(channel_types),
            limit=1000
        )
        channels = response.get("channels", [])
        simplified_channels = [{"name": channel.get("name")} for channel in channels]
        logger.debug(f"Returning {len(simplified_channels)} simplified channel records")
        return simplified_channels
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving Slack channels: {str(e)}")
        raise

@activity.defn
def search_slack(request: SlackSearchRequest) -> SlackSearchResult | str:
    if not request.query or not request.query.strip():
        return "Query parameter is required and cannot be empty"
    if request.count < 1 or request.count > 100:
        return "Count must be between 1 and 100"
    if request.sort not in ["timestamp", "score"]:
        return "Sort must be either 'timestamp' or 'score'"

    try:
        search_query = f"{request.query.strip()} -in:@Research Bot -is:dm"
        if request.channels:
            formatted_channels = [f"#{channel.strip()}" if not channel.strip().startswith('#') else channel.strip() for channel in request.channels.split(',')]
            channel_filter = " ".join([f"in:{channel}" for channel in formatted_channels])
            search_query = f"{search_query} {channel_filter}"
        if request.start_time:
            try:
                dt = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))
                search_query = f"{search_query} after:{dt.strftime('%Y-%m-%d')}"
            except ValueError:
                logger.warning(f"Invalid start_time ISO format: {request.start_time}, ignoring time filter")
        if request.end_time:
            try:
                dt = datetime.fromisoformat(request.end_time.replace('Z', '+00:00'))
                search_query = f"{search_query} before:{dt.strftime('%Y-%m-%d')}"
            except ValueError:
                logger.warning(f"Invalid end_time ISO format: {request.end_time}, ignoring time filter")

        logger.debug(f"Executing Slack search with query: '{search_query}'")
        client = get_slack_client()
        response = client.search_messages(query=search_query, sort=request.sort, count=request.count)
        messages = response.get("messages", {})
        matches = messages.get("matches", [])
        total = messages.get("total", 0)
        pagination = messages.get("pagination", {})
        has_more = pagination.get("total_count", 0) > len(matches)

        logger.debug(f"Search completed - found {total} total results, returning {len(matches)} matches")
        result = SlackSearchResult(query=search_query, total=total, matches=matches, pagination=pagination, has_more=has_more)
        return _format_search_results(result)
    except SlackApiError as e:
        logger.error(f"Slack API error during search: {e.response['error']}")
        return f"Slack API error: {e.response['error']}"
    except Exception as e:
        logger.error(f"Unexpected error during Slack search: {str(e)}")
        return f"Error searching Slack: {str(e)}"

@activity.defn
def get_thread_messages(params: ThreadInput) -> List[Dict[str, Any]]:
    try:
        url_parts = params.thread_url.split('/')
        if len(url_parts) < 6:
            raise ValueError("Invalid Slack thread URL format")
        channel_id = url_parts[-2]
        # Ensure correct timestamp format: 10 digits, period, 6 digits
        thread_ts = url_parts[-1][1:11] + '.' + url_parts[-1][11:17]
        client = get_slack_client()
        response = client.conversations_replies(channel=channel_id, ts=thread_ts)
        messages = response.get("messages", [])
        logger.debug(f"Retrieved {len(messages)} messages from thread")
        thread_messages = [{
            "text": msg.get("text"),
            "user": msg.get("user"),
            "timestamp": msg.get("ts"),
            "reply_count": msg.get("reply_count", 0),
            "reply_users_count": msg.get("reply_users_count", 0)
        } for msg in messages]
        logger.debug(f"Returning {len(thread_messages)} formatted messages")
        return thread_messages
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving thread messages: {str(e)}")
        raise

@activity.defn
def get_user_name(request: GetUserNameRequest) -> str:
    try:
        client = get_slack_client()
        response = client.users_info(user=request.user_id)
        user = response.get('user', {})
        return user.get('display_name') or user.get('real_name') or request.user_id
    except SlackApiError:
        logger.error(f"Failed to get user info for ID {request.user_id}")
        return request.user_id
    
def _format_search_results(result: SlackSearchResult) -> str:
        if result.total == 0:
            return f"No messages found for query: '{result.query}'"

        # Format results for LLM
        output_lines = [
            f"Found {result.total} messages for query: '{result.query}'",
            f"Showing top {len(result.matches)} results:\n"
        ]

        for i, match in enumerate(result.matches, 1):
            user = match.get('username', 'Unknown')
            channel = match.get('channel', {}).get('name', 'unknown-channel')
            text = match.get('text', '')[:200] + ('...' if len(match.get('text', '')) > 200 else '')
            timestamp = match.get('ts', '')
            permalink = match.get('permalink', '')

            # Format each result
            result_text = f"{i}. #{channel} - {user}"
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(float(timestamp))
                    result_text += f" ({dt.strftime('%Y-%m-%d %H:%M')})"
                except:
                    pass

            result_text += f"\n   {text}"
            if permalink:
                result_text += f"\n   Link: {permalink}"

            output_lines.append(result_text + "\n")

        if result.has_more:
            output_lines.append(f"... and {result.total - len(result.matches)} more results")

        return "\n".join(output_lines)

# todo: Should use instance methods once the Agent no longer rely on an instance method
def get_slack_client() -> WebClient:
    if not settings.slack_user_token or not settings.slack_user_token.startswith("xoxp-"):
        raise ValueError("slack_user_token is required and must be a user token")
    return WebClient(token=settings.slack_user_token)
