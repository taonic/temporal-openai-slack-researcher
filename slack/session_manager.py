from typing import Dict
from config import settings

from .session import Session
from temporalio.client import Client


class SessionManager:
    """Manages Slack sessions and their corresponding agent sessions."""
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.agent_runner = None
        self.sessions: Dict[str, Session] = {}
        self.client: Client = None
    
    async def __aenter__(self):
        await self._connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up sessions if needed
        self.sessions.clear()
    
    async def _connect(self) -> None:
        """Connect to the Temporal server."""
        if self.client is None:
            if settings.temporal_api_key:
                self.client = await Client.connect(
                    settings.temporal_host_port,
                    namespace=settings.temporal_namespace,
                    api_key=settings.temporal_api_key,
                    tls=True,
                )
            else:
                self.client = await Client.connect(
                    settings.temporal_host_port
                )

    async def get_session(self, slack_session_id: str) -> Session:
        """Get or create an agent session for the given Slack session ID."""
        if slack_session_id not in self.sessions:
            session = Session(
                client=self.client,
                session_id=slack_session_id
            )
            await session.start()
            self.sessions[slack_session_id] = session
        return self.sessions[slack_session_id]
    
    def remove_session(self, slack_session_id: str) -> None:
        """Remove a session from the manager."""
        if slack_session_id in self.sessions:
            del self.sessions[slack_session_id]
