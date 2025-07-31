import pytest
from unittest.mock import patch, MagicMock

from research_agents.tools import (
    get_slack_channels,
    search_slack,
    get_thread_messages,
    get_user_name,
    _format_search_results,
    get_slack_client,
    GetChannelsRequest,
    SlackSearchRequest,
    SlackSearchResult,
    ThreadInput,
    GetUserNameRequest
)

class TestSlackTools:
    @patch('research_agents.tools.get_slack_client')
    def test_get_slack_channels(self, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response data
        mock_response = {
            "channels": [
                {"id": "C123", "name": "general"},
                {"id": "C456", "name": "random"}
            ]
        }
        mock_client.conversations_list.return_value = mock_response
        
        # Call function
        result = get_slack_channels(GetChannelsRequest(include_archived=False))
        
        # Assertions
        mock_client.conversations_list.assert_called_once_with(
            exclude_archived=True,
            types="public_channel",
            limit=1000
        )
        assert len(result) == 2
        assert result[0]["name"] == "general"
        assert result[1]["name"] == "random"
    
    @patch('research_agents.tools.get_slack_client')
    def test_get_slack_channels_with_error(self, mock_get_client):
        # Setup mock with error
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.conversations_list.side_effect = Exception("API Error")
        
        # Call function and check exception
        with pytest.raises(Exception, match="API Error"):
            get_slack_channels(GetChannelsRequest(include_archived=True))
    
    @patch('research_agents.tools.get_slack_client')
    def test_search_slack_basic(self, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response data
        mock_response = {
            "messages": {
                "matches": [
                    {
                        "username": "user1",
                        "channel": {"name": "general"},
                        "text": "Hello world",
                        "ts": "1234567890.000000",
                        "permalink": "https://slack.com/link1"
                    }
                ],
                "total": 1,
                "pagination": {}
            }
        }
        mock_client.search_messages.return_value = mock_response
        
        # Call function
        result = search_slack(SlackSearchRequest(query="test query"))
        
        # Assertions
        mock_client.search_messages.assert_called_once()
        assert "Found 1 messages for query" in result
        assert "Hello world" in result
    
    @patch('research_agents.tools.get_slack_client')
    def test_search_slack_with_channels(self, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_messages.return_value = {"messages": {"matches": [], "total": 0}}
        
        # Call function with channel filter
        search_slack(SlackSearchRequest(query="test", channels="general,random"))
        
        # Check that channel filters were added to query
        call_args = mock_client.search_messages.call_args[1]
        assert "in:#general in:#random" in call_args["query"]
    
    @patch('research_agents.tools.get_slack_client')
    def test_search_slack_with_time_filters(self, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_messages.return_value = {"messages": {"matches": [], "total": 0}}
        
        # Call function with time filters
        search_slack(SlackSearchRequest(
            query="test",
            start_time="2023-01-01T00:00:00Z",
            end_time="2023-12-31T23:59:59Z"
        ))
        
        # Check that time filters were added to query
        call_args = mock_client.search_messages.call_args[1]
        assert "after:2023-01-01" in call_args["query"]
        assert "before:2023-12-31" in call_args["query"]
    
    def test_search_slack_validation(self):
        # Test empty query
        result = search_slack(SlackSearchRequest(query=""))
        assert "Query parameter is required" in result
        
        # Test invalid count
        result = search_slack(SlackSearchRequest(query="test", count=101))
        assert "Count must be between 1 and 100" in result
        
        # Test invalid sort
        result = search_slack(SlackSearchRequest(query="test", sort="invalid"))
        assert "Sort must be either" in result
    
    @patch('research_agents.tools.get_slack_client')
    def test_get_thread_messages(self, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response data
        mock_response = {
            "messages": [
                {
                    "text": "Thread starter",
                    "user": "U123",
                    "ts": "1234567890.000000",
                    "reply_count": 2,
                    "reply_users_count": 2
                },
                {
                    "text": "Reply 1",
                    "user": "U456",
                    "ts": "1609459300.000000"
                }
            ]
        }
        mock_client.conversations_replies.return_value = mock_response
        
        # Call function
        thread_url = "https://workspace.slack.com/archives/C123/p1234567890000000"
        result = get_thread_messages(ThreadInput(thread_url=thread_url))
        
        # Assertions
        mock_client.conversations_replies.assert_called_once_with(
            channel="C123", 
            ts="1234567890.000000"
        )
        assert len(result) == 2
        assert result[0]["text"] == "Thread starter"
        assert result[1]["text"] == "Reply 1"
    
    @patch('research_agents.tools.get_slack_client')
    def test_get_thread_messages_invalid_url(self, mock_get_client):
        # Setup mock
        mock_get_client.return_value = MagicMock()
        
        # Test with invalid URL
        with pytest.raises(ValueError, match="Invalid Slack thread URL format"):
            get_thread_messages(ThreadInput(thread_url="https://invalid.url"))
    
    @patch('research_agents.tools.get_slack_client')
    def test_get_user_name(self, mock_get_client):
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response data
        mock_response = {
            "user": {
                "id": "U123",
                "display_name": "display_name",
                "real_name": "real_name"
            }
        }
        mock_client.users_info.return_value = mock_response
        
        # Call function
        result = get_user_name(GetUserNameRequest(user_id="U123"))
        
        # Assertions
        mock_client.users_info.assert_called_once_with(user="U123")
        assert result == "display_name"
    
    def test_format_search_results(self):
        # Test with empty results
        empty_result = SlackSearchResult(query="test", total=0, matches=[])
        formatted = _format_search_results(empty_result)
        assert "No messages found" in formatted
        
        # Test with results
        matches = [
            {
                "username": "user1",
                "channel": {"name": "general"},
                "text": "Hello world",
                "ts": "1234567890.000000",
                "permalink": "https://slack.com/link1"
            },
            {
                "username": "user2",
                "channel": {"name": "random"},
                "text": "Another message",
                "ts": "1609459300.000000",
                "permalink": "https://slack.com/link2"
            }
        ]
        result = SlackSearchResult(query="test", total=10, matches=matches, has_more=True)
        formatted = _format_search_results(result)
        
        # Assertions
        assert "Found 10 messages for query" in formatted
        assert "Showing top 2 results" in formatted
        assert "#general - user1" in formatted
        assert "#random - user2" in formatted
        assert "Hello world" in formatted
        assert "Another message" in formatted
        assert "... and 8 more results" in formatted
    
    @patch('research_agents.tools.settings')
    def test_get_slack_client(self, mock_settings):
        # Test with valid token
        mock_settings.slack_user_token = "xoxp-valid-token"
        client = get_slack_client()
        assert client is not None
        
        # Test with invalid token
        mock_settings.slack_user_token = "invalid-token"
        with pytest.raises(ValueError, match="slack_user_token is required"):
            get_slack_client()
        
        # Test with empty token
        mock_settings.slack_user_token = ""
        with pytest.raises(ValueError, match="slack_user_token is required"):
            get_slack_client()
