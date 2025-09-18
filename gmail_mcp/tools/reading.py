"""MCP tools for email reading operations."""

from typing import Optional, List
import json
import logging

from mcp.server import FastMCP
from fastapi import HTTPException
from mcp.server.fastmcp.server import Context

from ..services import GmailService
from ..models import EmailListRequest, SearchEmailsRequest, MessageFormat
from ..dependencies import get_access_token, get_gmail_service


logger = logging.getLogger(__name__)


def register_reading_tools(mcp: FastMCP):
    """Register email reading tools with MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def get_emails(
        ctx: Context,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Get list of emails from Gmail.

        Args:
            max_results: Maximum number of emails to return (1-500)
            label_ids: Filter by label IDs (e.g., ['INBOX', 'UNREAD'])
            query: Gmail search query (e.g., 'from:example@gmail.com')
            include_spam_trash: Include spam and trash emails
            page_token: Token for pagination
            format: Message format (MINIMAL, COMPACT, FULL, RAW, METADATA)

        Returns:
            JSON string with email list response

        Format Details:
            - MINIMAL: id, threadId, labelIds only
            - COMPACT: MINIMAL + subject, sender, date, body_text (recommended)
            - FULL: Complete message including body, headers, attachments
            - RAW: Raw RFC2822 message
            - METADATA: Headers and labels only (no body)
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info(f"Fetching {max_results} emails with format {format}")

            # GmailService is injected with the access token already configured

            # Create request object
            email_request = EmailListRequest(
                max_results=max_results,
                label_ids=label_ids or [],
                q=query,
                include_spam_trash=include_spam_trash,
                page_token=page_token,
            )

            # Get emails with specified format
            response = await gmail_service.list_messages(email_request, format.value)

            logger.info(f"Retrieved {len(response.messages)} emails")

            return json.dumps(response.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error getting emails: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get emails: {str(e)}")

    @mcp.tool()
    async def get_email_by_id(
        ctx: Context,
        email_id: str,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Get specific email by ID.

        Args:
            email_id: Gmail message ID
            format: Email format (MINIMAL, COMPACT, FULL, RAW, METADATA)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with email details

        Format Details:
            - MINIMAL: id, threadId, labelIds only (fastest)
            - COMPACT: MINIMAL + subject, sender, date, body_text (recommended)
            - FULL: Complete message including body, headers, attachments
            - RAW: Raw RFC2822 message
            - METADATA: Headers and labels only (no body)
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info(f"Fetching email {email_id} with format {format}")

            # GmailService is injected with the access token already configured
            message = await gmail_service.get_message(email_id, format.value)

            logger.info(f"Retrieved email: {message.subject}")

            return json.dumps(message.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error getting email {email_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get email: {str(e)}")

    @mcp.tool()
    async def search_emails(
        ctx: Context,
        query: str,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Search emails using Gmail search syntax.

        Args:
            query: Gmail search query (e.g., 'from:example@gmail.com subject:urgent')
            max_results: Maximum number of results (1-500)
            label_ids: Filter by label IDs
            include_spam_trash: Include spam and trash in search
            page_token: Token for pagination
            format: Message format (MINIMAL, COMPACT, FULL, RAW, METADATA)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with search results

        Format Details:
            - MINIMAL: id, threadId, labelIds only (fastest, but limited info)
            - COMPACT: MINIMAL + subject, sender, date, body_text (recommended for search)
            - FULL: Complete message including body, headers, attachments
            - RAW: Raw RFC2822 message
            - METADATA: Headers and labels only (no body)
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info(f"Searching emails with query: {query}, format: {format}")

            # GmailService is injected with the access token already configured

            search_request = SearchEmailsRequest(
                query=query,
                max_results=max_results,
                label_ids=label_ids or [],
                include_spam_trash=include_spam_trash,
                page_token=page_token,
            )

            response = await gmail_service.search_messages(search_request, format.value)

            logger.info(f"Found {len(response.messages)} matching emails")

            return json.dumps(response.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to search emails: {str(e)}")

    @mcp.tool()
    async def get_labels(ctx: Context) -> str:
        """Get all Gmail labels.

        Args:
            ctx: MCP context for logging and progress

        Returns:
            JSON string with labels list
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info("Fetching Gmail labels")

            # GmailService is injected with the access token already configured
            labels = await gmail_service.list_labels()

            logger.info(f"Retrieved {len(labels)} labels")

            return json.dumps([label.model_dump() for label in labels], default=str)

        except Exception as e:
            logger.error(f"Error getting labels: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get labels: {str(e)}")

    @mcp.tool()
    async def get_profile(ctx: Context) -> str:
        """Get Gmail profile information.

        Args:
            ctx: MCP context for logging and progress

        Returns:
            JSON string with profile information
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info("Fetching Gmail profile")

            # GmailService is injected with the access token already configured
            profile = await gmail_service.get_profile()

            logger.info(f"Retrieved profile for {profile.email_address}")

            return json.dumps(profile.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")
