"""MCP tools for advanced Gmail operations (drafts, threads, attachments)."""

from typing import Optional, List
import json
import logging

from mcp.server import FastMCP
from fastapi import HTTPException
from mcp.server.fastmcp.server import Context

from ..services import GmailService
from ..models import ForwardEmailRequest, CreateDraftRequest, ThreadListRequest
from ..dependencies import get_access_token, get_gmail_service


logger = logging.getLogger(__name__)


def register_advanced_tools(mcp: FastMCP):
    """Register advanced Gmail tools with MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def forward_email(
        ctx: Context,
        message_id: str,
        to: List[str],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        additional_message: Optional[str] = None,
    ) -> str:
        """Forward an email to other recipients.

        Args:
            message_id: ID of email to forward
            to: List of recipient email addresses
            cc: CC recipients
            bcc: BCC recipients
            additional_message: Additional message to include with forward
            ctx: MCP context for logging and progress

        Returns:
            JSON string with forward status and message ID
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Forward the email using the Gmail service

            request = ForwardEmailRequest(
                to=to,
                cc=cc,
                bcc=bcc,
                additional_message=additional_message,
            )

            forwarded_message_id = await gmail_service.forward_message(message_id, request)

            result = {
                "success": True,
                "forwarded_message_id": forwarded_message_id,
                "original_message_id": message_id,
                "message": f"Email forwarded successfully to {', '.join(to)}",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in forward_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def move_to_folder(
        ctx: Context,
        message_id: str,
        folder_label_id: str,
        remove_inbox: bool = True,
    ) -> str:
        """Move an email to a specific folder/label.

        Args:
            message_id: Message ID to move
            folder_label_id: Target folder/label ID (e.g., 'TRASH', 'SPAM', or custom label ID)
            remove_inbox: Whether to remove from INBOX when moving
            ctx: MCP context for logging and progress

        Returns:
            JSON string with move status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:

            from ..models import ModifyLabelsRequest

            add_labels = [folder_label_id]
            remove_labels = []

            if remove_inbox and folder_label_id not in ["INBOX"]:
                remove_labels.append("INBOX")

            request = ModifyLabelsRequest(
                add_label_ids=add_labels,
                remove_label_ids=remove_labels if remove_labels else None,
            )

            updated_message = await gmail_service.modify_message_labels(message_id, request)

            result = {
                "success": True,
                "message_id": message_id,
                "moved_to": folder_label_id,
                "current_labels": updated_message.label_ids,
                "message": f"Email moved to {folder_label_id}",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in move_to_folder: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def get_threads(
        ctx: Context,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
    ) -> str:
        """Get email threads/conversations.

        Args:
            max_results: Maximum number of threads to return (1-500)
            label_ids: Filter by label IDs
            query: Gmail search query
            include_spam_trash: Include spam and trash
            page_token: Token for pagination
            ctx: MCP context for logging and progress

        Returns:
            JSON string with threads list
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # GmailService is injected via dependency injection

            request = ThreadListRequest(
                max_results=max_results,
                label_ids=label_ids,
                q=query,
                include_spam_trash=include_spam_trash,
                page_token=page_token,
            )

            response = await gmail_service.list_threads(request)

            result = {
                "threads": [thread.model_dump() for thread in response.threads],
                "next_page_token": response.next_page_token,
                "result_size_estimate": response.result_size_estimate,
                "count": len(response.threads),
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_threads: {e}")
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def create_draft(
        ctx: Context,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> str:
        """Create a draft email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            cc: CC recipients
            bcc: BCC recipients
            thread_id: Thread ID for replies
            in_reply_to: Message ID being replied to
            ctx: MCP context for logging and progress

        Returns:
            JSON string with draft creation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            if not body_text and not body_html:
                return json.dumps({"error": "Either body_text or body_html must be provided"})

            # GmailService is injected via dependency injection

            request = CreateDraftRequest(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                thread_id=thread_id,
                in_reply_to=in_reply_to,
            )

            draft_id = await gmail_service.create_draft(request)

            result = {
                "success": True,
                "draft_id": draft_id,
                "message": f"Draft created successfully for {', '.join(to)}",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in create_draft: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def get_drafts(
        ctx: Context,
        max_results: int = 10,
        page_token: Optional[str] = None,
    ) -> str:
        """Get list of draft emails.

        Args:
            max_results: Maximum number of drafts to return
            page_token: Token for pagination
            ctx: MCP context for logging and progress

        Returns:
            JSON string containing drafts list
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # GmailService is injected via dependency injection

            response = await gmail_service.list_drafts(max_results, page_token)

            result = {
                "drafts": [draft.model_dump() for draft in response.drafts],
                "next_page_token": response.next_page_token,
                "result_size_estimate": response.result_size_estimate,
                "count": len(response.drafts),
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_drafts: {e}")
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def send_draft(
        ctx: Context,
        draft_id: str,
    ) -> str:
        """Send an existing draft email.

        Args:
            draft_id: Draft ID to send
            ctx: MCP context for logging and progress

        Returns:
            JSON string with send status and message ID
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Send the draft email

            message_id = await gmail_service.send_draft(draft_id)

            result = {
                "success": True,
                "message_id": message_id,
                "draft_id": draft_id,
                "message": "Draft sent successfully",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in send_draft: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def get_attachments(
        ctx: Context,
        message_id: str,
        attachment_id: Optional[str] = None,
    ) -> str:
        """Download email attachments.

        Args:
            message_id: Message ID containing attachments
            attachment_id: Specific attachment ID (if None, returns info about all attachments)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with attachment data or list of attachments
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # GmailService is injected via dependency injection

            if attachment_id:
                # Download specific attachment
                attachment = await gmail_service.get_attachment(message_id, attachment_id)

                result = {
                    "success": True,
                    "attachment": attachment.model_dump(),
                    "message": f"Attachment {attachment_id} downloaded successfully",
                }
            else:
                # Get message to list all attachments
                message = await gmail_service.get_message(message_id)

                result = {
                    "success": True,
                    "message_id": message_id,
                    "attachments": [att.model_dump() for att in message.attachments],
                    "count": len(message.attachments),
                    "message": f"Found {len(message.attachments)} attachments",
                }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_attachments: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
