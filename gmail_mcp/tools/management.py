"""MCP tools for email sending and management operations."""

from typing import Optional, List
import json
import logging

from mcp.server import FastMCP
from fastapi import HTTPException, Depends

from ..services import GmailService
from ..models import SendEmailRequest, ModifyLabelsRequest, CreateLabelRequest
from ..dependencies import get_gmail_service


logger = logging.getLogger(__name__)




def register_management_tools(mcp: FastMCP):
    """Register email management tools with MCP server.
    
    Args:
        mcp: FastMCP server instance
    """
    
    @mcp.tool()
    async def send_email(
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Send an email.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            cc: CC recipients
            bcc: BCC recipients  
            attachments: List of file paths to attach
            ctx: MCP context for logging and progress
            gmail_service: GmailService instance (injected)
            
        Returns:
            JSON string with send status and message ID
        """
        try:
            if not body_text and not body_html:
                return json.dumps({"error": "Either body_text or body_html must be provided"})
            
            # GmailService is injected with the access token already configured
            
            request = SendEmailRequest(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                attachments=attachments
            )
            
            message_id = await gmail_service.send_message(request)
            
            result = {
                "success": True,
                "message_id": message_id,
                "message": f"Email sent successfully to {', '.join(to)}"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
    @mcp.tool()
    async def reply_to_email(
        message_id: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        reply_all: bool = False,
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Reply to an email.
        
        Args:
            message_id: ID of message to reply to
            body_text: Plain text reply body
            body_html: HTML reply body
            reply_all: Reply to all recipients
            token_info: Token information (injected)
            
        Returns:
            JSON string with reply status
        """
        try:
            if not body_text and not body_html:
                return json.dumps({"error": "Either body_text or body_html must be provided"})
            
            # GmailService is injected via dependency injection
            
            # Get original message to extract reply info
            original_message = await gmail_service.get_message(message_id)
            
            # Prepare reply
            to_addresses = [original_message.sender] if original_message.sender else []
            
            if reply_all and original_message.recipient:
                # Add other recipients for reply-all (simplified)
                # In production, you'd parse all To/CC recipients from headers
                pass
            
            subject = original_message.subject or ""
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"
            
            request = SendEmailRequest(
                to=to_addresses,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                thread_id=original_message.thread_id,
                in_reply_to=message_id
            )
            
            reply_message_id = await gmail_service.send_message(request)
            
            result = {
                "success": True,
                "reply_message_id": reply_message_id,
                "original_message_id": message_id,
                "message": f"Reply sent successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in reply_to_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
    
    @mcp.tool()
    async def mark_as_read(
        message_id: str,
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Mark an email as read.
        
        Args:
            message_id: Message ID to mark as read
            token_info: Token information (injected)
            
        Returns:
            JSON string with operation status
        """
        try:
            # GmailService is injected via dependency injection
            
            request = ModifyLabelsRequest(remove_label_ids=["UNREAD"])
            await gmail_service.modify_message_labels(message_id, request)
            
            result = {
                "success": True,
                "message_id": message_id,
                "message": "Email marked as read"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in mark_as_read: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
    
    @mcp.tool()
    async def mark_as_unread(
        message_id: str,
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Mark an email as unread.
        
        Args:
            message_id: Message ID to mark as unread
            token_info: Token information (injected)
            
        Returns:
            JSON string with operation status
        """
        try:
            # GmailService is injected via dependency injection
            
            request = ModifyLabelsRequest(add_label_ids=["UNREAD"])
            await gmail_service.modify_message_labels(message_id, request)
            
            result = {
                "success": True,
                "message_id": message_id,
                "message": "Email marked as unread"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in mark_as_unread: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
    
    @mcp.tool()
    async def archive_email(
        message_id: str,
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Archive an email (remove from INBOX).
        
        Args:
            message_id: Message ID to archive
            token_info: Token information (injected)
            
        Returns:
            JSON string with operation status
        """
        try:
            # GmailService is injected via dependency injection
            
            request = ModifyLabelsRequest(remove_label_ids=["INBOX"])
            await gmail_service.modify_message_labels(message_id, request)
            
            result = {
                "success": True,
                "message_id": message_id,
                "message": "Email archived successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in archive_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
    
    @mcp.tool()
    async def delete_email(
        message_id: str,
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Delete an email permanently.
        
        Args:
            message_id: Message ID to delete
            token_info: Token information (injected)
            
        Returns:
            JSON string with operation status
        """
        try:
            # GmailService is injected via dependency injection
            
            success = await gmail_service.delete_message(message_id)
            
            if success:
                result = {
                    "success": True,
                    "message_id": message_id,
                    "message": "Email deleted successfully"
                }
            else:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "message": "Failed to delete email"
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in delete_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
    
    @mcp.tool()
    async def add_label(
        message_id: str,
        label_ids: List[str],
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Add labels to an email.
        
        Args:
            message_id: Message ID
            label_ids: List of label IDs to add
            token_info: Token information (injected)
            
        Returns:
            JSON string with operation status
        """
        try:
            # GmailService is injected via dependency injection
            
            request = ModifyLabelsRequest(add_label_ids=label_ids)
            updated_message = await gmail_service.modify_message_labels(message_id, request)
            
            result = {
                "success": True,
                "message_id": message_id,
                "added_labels": label_ids,
                "current_labels": updated_message.label_ids,
                "message": f"Labels {', '.join(label_ids)} added successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in add_label: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
    
    @mcp.tool()
    async def remove_label(
        message_id: str,
        label_ids: List[str],
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Remove labels from an email.
        
        Args:
            message_id: Message ID
            label_ids: List of label IDs to remove
            token_info: Token information (injected)
            
        Returns:
            JSON string with operation status
        """
        try:
            # GmailService is injected via dependency injection
            
            request = ModifyLabelsRequest(remove_label_ids=label_ids)
            updated_message = await gmail_service.modify_message_labels(message_id, request)
            
            result = {
                "success": True,
                "message_id": message_id,
                "removed_labels": label_ids,
                "current_labels": updated_message.label_ids,
                "message": f"Labels {', '.join(label_ids)} removed successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in remove_label: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
    
    @mcp.tool()
    async def create_label(
        name: str,
        message_list_visibility: str = "show",
        label_list_visibility: str = "labelShow",
        gmail_service: GmailService = Depends(get_gmail_service)
    ) -> str:
        """Create a new Gmail label.
        
        Args:
            name: Label name
            message_list_visibility: Message list visibility (show/hide)
            label_list_visibility: Label list visibility (labelShow/labelHide)
            token_info: Token information (injected)
            
        Returns:
            JSON string with created label information
        """
        try:
            # GmailService is injected via dependency injection
            
            request = CreateLabelRequest(
                name=name,
                message_list_visibility=message_list_visibility,
                label_list_visibility=label_list_visibility
            )
            
            label = await gmail_service.create_label(request)
            
            result = {
                "success": True,
                "label": label.model_dump(),
                "message": f"Label '{name}' created successfully"
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error in create_label: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)