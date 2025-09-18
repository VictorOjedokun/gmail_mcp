"""Gmail API service layer."""

from typing import List, Optional, Dict, Any
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import logging

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pydantic import BaseModel

from ..models import (
    Message,
    Thread,
    Label,
    Draft,
    Profile,
    AttachmentData,
    MessagePart,
    MessageHeader,
    SendEmailRequest,
    SearchEmailsRequest,
    EmailListRequest,
    ModifyLabelsRequest,
    CreateLabelRequest,
    ForwardEmailRequest,
    CreateDraftRequest,
    ThreadListRequest,
    EmailListResponse,
    ThreadListResponse,
    LabelListResponse,
    DraftListResponse,
)
from ..auth import TokenInfo


logger = logging.getLogger(__name__)


class GmailService:
    """Gmail API service wrapper."""

    def __init__(self, token_info: TokenInfo):
        """Initialize Gmail service with token.

        Args:
            token_info: Valid token information
        """
        self.token_info = token_info
        self.credentials = Credentials(token=token_info.access_token)
        self.service = build("gmail", "v1", credentials=self.credentials)

    def _parse_message_headers(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        """Parse message headers into a dictionary.

        Args:
            headers: List of header dictionaries

        Returns:
            Dictionary of header name -> value
        """
        return {header["name"].lower(): header["value"] for header in headers}

    def _extract_message_parts(self, payload: Dict[str, Any]) -> MessagePart:
        """Extract message parts from Gmail API payload.

        Args:
            payload: Gmail API message payload

        Returns:
            MessagePart object
        """
        parts = []
        if "parts" in payload:
            for part in payload["parts"]:
                parts.append(self._extract_message_parts(part))

        return MessagePart(
            part_id=payload.get("partId"),
            mime_type=payload.get("mimeType", ""),
            filename=payload.get("filename"),
            headers=payload.get("headers", []),
            body=payload.get("body", {}),
            parts=parts if parts else None,
        )

    def _extract_message_content(
        self, payload: Dict[str, Any]
    ) -> tuple[str, str, List[AttachmentData]]:
        """Extract text content and attachments from message payload.

        Args:
            payload: Gmail API message payload

        Returns:
            Tuple of (plain_text, html_text, attachments)
        """
        plain_text = ""
        html_text = ""
        attachments = []

        def extract_from_part(part: Dict[str, Any]):
            nonlocal plain_text, html_text, attachments

            mime_type = part.get("mimeType", "")
            body = part.get("body", {})

            if mime_type == "text/plain" and "data" in body:
                plain_text += base64.urlsafe_b64decode(body["data"]).decode("utf-8")
            elif mime_type == "text/html" and "data" in body:
                html_text += base64.urlsafe_b64decode(body["data"]).decode("utf-8")
            elif part.get("filename") and "attachmentId" in body:
                attachments.append(
                    AttachmentData(attachment_id=body["attachmentId"], size=body.get("size", 0))
                )

            # Recursively process parts
            if "parts" in part:
                for subpart in part["parts"]:
                    extract_from_part(subpart)

        extract_from_part(payload)
        return plain_text, html_text, attachments

    def _parse_message(self, msg_data: Dict[str, Any], format: str = "full") -> Message:
        """Parse Gmail API message data into Message object.

        Args:
            msg_data: Gmail API message data
            format: Format level for parsing (minimal, compact, full, metadata, raw)

        Returns:
            Message object with appropriate level of detail
        """
        payload = msg_data.get("payload", {})
        headers = self._parse_message_headers(payload.get("headers", []))

        # Parse date
        date = None
        if "internalDate" in msg_data:
            timestamp = int(msg_data["internalDate"]) / 1000
            date = datetime.fromtimestamp(timestamp)

        # Base minimal data
        base_data = {
            "id": msg_data["id"],
            "thread_id": msg_data["threadId"],
            "label_ids": msg_data.get("labelIds", []),
            "snippet": msg_data.get("snippet"),
            "history_id": msg_data.get("historyId"),
            "internal_date": date,
            "size_estimate": msg_data.get("sizeEstimate"),
        }

        if format == "minimal":
            # Return minimal data only
            return Message(
                **base_data,
                payload=None,
                raw=None,
                subject=None,
                sender=None,
                recipient=None,
                date=date,
                body_text=None,
                body_html=None,
                attachments=[],
            )
        
        elif format == "compact":
            # Extract minimal content (text only, no attachments)
            plain_text = ""
            if payload:
                plain_text, _, _ = self._extract_message_content(payload)
            
            return Message(
                **base_data,
                payload=None,  # Don't include full payload for efficiency
                raw=None,
                subject=headers.get("subject"),
                sender=headers.get("from"),
                recipient=headers.get("to"),
                date=date,
                body_text=plain_text,
                body_html=None,  # Skip HTML for efficiency
                attachments=[],  # Skip attachments for efficiency
            )
        
        else:
            # Full parsing for FULL, METADATA, RAW formats
            plain_text, html_text, attachments = self._extract_message_content(payload)

            return Message(
                **base_data,
                payload=self._extract_message_parts(payload),
                raw=msg_data.get("raw"),
                subject=headers.get("subject"),
                sender=headers.get("from"),
                recipient=headers.get("to"),
                date=date,
                body_text=plain_text,
                body_html=html_text,
                attachments=attachments,
            )

    async def get_profile(self) -> Profile:
        """Get Gmail profile information.

        Returns:
            Profile object
        """
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            return Profile(
                email_address=profile["emailAddress"],
                messages_total=profile["messagesTotal"],
                threads_total=profile["threadsTotal"],
                history_id=profile["historyId"],
            )
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            raise

    async def list_messages(self, request: EmailListRequest, format: str = "full") -> EmailListResponse:
        """List messages based on request criteria.

        Args:
            request: Email list request
            format: Message format (minimal, compact, full, raw, metadata)

        Returns:
            EmailListResponse with messages
        """
        try:
            query_params = {
                "userId": "me",
                "maxResults": request.max_results,
                "includeSpamTrash": request.include_spam_trash,
            }

            if request.label_ids:
                query_params["labelIds"] = request.label_ids
            if request.q:
                query_params["q"] = request.q
            if request.page_token:
                query_params["pageToken"] = request.page_token

            result = self.service.users().messages().list(**query_params).execute()

            messages = []
            for msg in result.get("messages", []):
                # Map our custom formats to Gmail API formats
                gmail_api_format = format
                if format == "compact":
                    gmail_api_format = "metadata"  # Get headers but not full body data
                
                # Get message details with specified format
                full_msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format=gmail_api_format)
                    .execute()
                )
                messages.append(self._parse_message(full_msg, format))

            return EmailListResponse(
                messages=messages,
                next_page_token=result.get("nextPageToken"),
                result_size_estimate=result.get("resultSizeEstimate"),
            )
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            raise

    async def get_message(self, message_id: str, format: str = "full") -> Message:
        """Get a specific message by ID.

        Args:
            message_id: Message ID
            format: Message format (minimal, compact, full, raw, metadata)

        Returns:
            Message object
        """
        try:
            # Map our custom formats to Gmail API formats
            gmail_api_format = format
            if format == "compact":
                gmail_api_format = "metadata"  # Get headers but not full body data
            
            msg_data = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format=gmail_api_format)
                .execute()
            )
            return self._parse_message(msg_data, format)
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            raise

    async def search_messages(self, request: SearchEmailsRequest, format: str = "full") -> EmailListResponse:
        """Search messages using Gmail query syntax.

        Args:
            request: Search request
            format: Message format (minimal, compact, full, raw, metadata)

        Returns:
            EmailListResponse with matching messages
        """
        try:
            query_params = {
                "userId": "me",
                "q": request.query,
                "maxResults": request.max_results,
                "includeSpamTrash": request.include_spam_trash,
            }

            if request.page_token:
                query_params["pageToken"] = request.page_token

            result = self.service.users().messages().list(**query_params).execute()

            messages = []
            for msg in result.get("messages", []):
                # Map our custom formats to Gmail API formats
                gmail_api_format = format
                if format == "compact":
                    gmail_api_format = "metadata"  # Get headers but not full body data
                
                full_msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format=gmail_api_format)
                    .execute()
                )
                messages.append(self._parse_message(full_msg, format))

            return EmailListResponse(
                messages=messages,
                next_page_token=result.get("nextPageToken"),
                result_size_estimate=result.get("resultSizeEstimate"),
            )
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise

    async def send_message(self, request: SendEmailRequest) -> str:
        """Send an email message.

        Args:
            request: Send email request

        Returns:
            Message ID of sent email
        """
        try:
            # Create MIME message
            if request.body_html:
                msg = MIMEMultipart("alternative")
                if request.body_text:
                    text_part = MIMEText(request.body_text, "plain")
                    msg.attach(text_part)
                html_part = MIMEText(request.body_html, "html")
                msg.attach(html_part)
            else:
                msg = MIMEText(request.body_text or "", "plain")

            # Set headers
            msg["To"] = ", ".join(request.to)
            if request.cc:
                msg["Cc"] = ", ".join(request.cc)
            if request.bcc:
                msg["Bcc"] = ", ".join(request.bcc)
            msg["Subject"] = request.subject

            if request.in_reply_to:
                msg["In-Reply-To"] = request.in_reply_to
            if request.thread_id:
                msg["References"] = request.thread_id

            # Handle attachments
            if request.attachments:
                if not isinstance(msg, MIMEMultipart):
                    # Convert to multipart if we have attachments
                    original_msg = msg
                    msg = MIMEMultipart()
                    msg.attach(original_msg)
                    # Copy headers
                    for key, value in original_msg.items():
                        msg[key] = value

                for attachment_path in request.attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, "rb") as f:
                            attachment = MIMEBase("application", "octet-stream")
                            attachment.set_payload(f.read())
                            encoders.encode_base64(attachment)
                            attachment.add_header(
                                "Content-Disposition",
                                f"attachment; filename= {os.path.basename(attachment_path)}",
                            )
                            msg.attach(attachment)

            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

            send_request = {"raw": raw_message}
            if request.thread_id:
                send_request["threadId"] = request.thread_id

            result = self.service.users().messages().send(userId="me", body=send_request).execute()

            return result["id"]
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def modify_message_labels(self, message_id: str, request: ModifyLabelsRequest) -> Message:
        """Modify message labels.

        Args:
            message_id: Message ID
            request: Label modification request

        Returns:
            Updated Message object
        """
        try:
            modify_request = {}
            if request.add_label_ids:
                modify_request["addLabelIds"] = request.add_label_ids
            if request.remove_label_ids:
                modify_request["removeLabelIds"] = request.remove_label_ids

            result = (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body=modify_request)
                .execute()
            )

            return self._parse_message(result)
        except Exception as e:
            logger.error(f"Error modifying message labels: {e}")
            raise

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message.

        Args:
            message_id: Message ID

        Returns:
            True if successful
        """
        try:
            self.service.users().messages().delete(userId="me", id=message_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            raise

    async def list_labels(self) -> LabelListResponse:
        """List all labels.

        Returns:
            LabelListResponse with labels
        """
        try:
            result = self.service.users().labels().list(userId="me").execute()

            labels = []
            for label_data in result.get("labels", []):
                label = Label(
                    id=label_data["id"],
                    name=label_data["name"],
                    type=label_data["type"].lower(),
                    message_list_visibility=label_data.get("messageListVisibility"),
                    label_list_visibility=label_data.get("labelListVisibility"),
                    messages_total=label_data.get("messagesTotal"),
                    messages_unread=label_data.get("messagesUnread"),
                    threads_total=label_data.get("threadsTotal"),
                    threads_unread=label_data.get("threadsUnread"),
                )
                labels.append(label)

            return LabelListResponse(labels=labels)
        except Exception as e:
            logger.error(f"Error listing labels: {e}")
            raise

    async def create_label(self, request: CreateLabelRequest) -> Label:
        """Create a new label.

        Args:
            request: Create label request

        Returns:
            Created Label object
        """
        try:
            label_object = {
                "name": request.name,
                "messageListVisibility": request.message_list_visibility,
                "labelListVisibility": request.label_list_visibility,
            }

            result = self.service.users().labels().create(userId="me", body=label_object).execute()

            return Label(
                id=result["id"],
                name=result["name"],
                type="user",
                message_list_visibility=result.get("messageListVisibility"),
                label_list_visibility=result.get("labelListVisibility"),
            )
        except Exception as e:
            logger.error(f"Error creating label: {e}")
            raise

    async def forward_message(self, message_id: str, request: ForwardEmailRequest) -> str:
        """Forward an email message.

        Args:
            message_id: ID of message to forward
            request: Forward email request

        Returns:
            Message ID of forwarded email
        """
        try:
            # Get original message
            original_message = await self.get_message(message_id)

            # Create forwarded message
            if original_message.body_html:
                msg = MIMEMultipart("alternative")

                # Add additional message if provided
                forward_content = ""
                if request.additional_message:
                    forward_content = f"{request.additional_message}\n\n"

                forward_content += f"---------- Forwarded message ---------\n"
                forward_content += f"From: {original_message.sender}\n"
                forward_content += f"Date: {original_message.date}\n"
                forward_content += f"Subject: {original_message.subject}\n"
                forward_content += f"To: {original_message.recipient}\n\n"

                # Text part
                text_part = MIMEText(forward_content + (original_message.body_text or ""), "plain")
                msg.attach(text_part)

                # HTML part
                html_content = forward_content.replace("\n", "<br>") + (
                    original_message.body_html or ""
                )
                html_part = MIMEText(html_content, "html")
                msg.attach(html_part)
            else:
                forward_content = ""
                if request.additional_message:
                    forward_content = f"{request.additional_message}\n\n"

                forward_content += f"---------- Forwarded message ---------\n"
                forward_content += f"From: {original_message.sender}\n"
                forward_content += f"Date: {original_message.date}\n"
                forward_content += f"Subject: {original_message.subject}\n"
                forward_content += f"To: {original_message.recipient}\n\n"
                forward_content += original_message.body_text or ""

                msg = MIMEText(forward_content, "plain")

            # Set headers
            msg["To"] = ", ".join(request.to)
            if request.cc:
                msg["Cc"] = ", ".join(request.cc)
            if request.bcc:
                msg["Bcc"] = ", ".join(request.bcc)

            subject = original_message.subject or ""
            if not subject.startswith("Fwd:"):
                subject = f"Fwd: {subject}"
            msg["Subject"] = subject

            # Encode and send
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

            result = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            return result["id"]
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            raise

    async def list_threads(self, request: ThreadListRequest) -> ThreadListResponse:
        """List email threads.

        Args:
            request: Thread list request

        Returns:
            ThreadListResponse with threads
        """
        try:
            query_params = {
                "userId": "me",
                "maxResults": request.max_results,
                "includeSpamTrash": request.include_spam_trash,
            }

            if request.label_ids:
                query_params["labelIds"] = request.label_ids
            if request.q:
                query_params["q"] = request.q
            if request.page_token:
                query_params["pageToken"] = request.page_token

            result = self.service.users().threads().list(**query_params).execute()

            threads = []
            for thread_data in result.get("threads", []):
                # Get full thread details
                full_thread = (
                    self.service.users()
                    .threads()
                    .get(userId="me", id=thread_data["id"], format="full")
                    .execute()
                )

                messages = []
                for msg_data in full_thread.get("messages", []):
                    messages.append(self._parse_message(msg_data))

                thread = Thread(
                    id=full_thread["id"],
                    snippet=full_thread.get("snippet"),
                    history_id=full_thread.get("historyId"),
                    messages=messages,
                )
                threads.append(thread)

            return ThreadListResponse(
                threads=threads,
                next_page_token=result.get("nextPageToken"),
                result_size_estimate=result.get("resultSizeEstimate"),
            )
        except Exception as e:
            logger.error(f"Error listing threads: {e}")
            raise

    async def create_draft(self, request: CreateDraftRequest) -> str:
        """Create a draft email.

        Args:
            request: Create draft request

        Returns:
            Draft ID
        """
        try:
            # Create MIME message
            if request.body_html:
                msg = MIMEMultipart("alternative")
                if request.body_text:
                    text_part = MIMEText(request.body_text, "plain")
                    msg.attach(text_part)
                html_part = MIMEText(request.body_html, "html")
                msg.attach(html_part)
            else:
                msg = MIMEText(request.body_text or "", "plain")

            # Set headers
            msg["To"] = ", ".join(request.to)
            if request.cc:
                msg["Cc"] = ", ".join(request.cc)
            if request.bcc:
                msg["Bcc"] = ", ".join(request.bcc)
            msg["Subject"] = request.subject

            if request.in_reply_to:
                msg["In-Reply-To"] = request.in_reply_to
            if request.thread_id:
                msg["References"] = request.thread_id

            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

            draft_request = {"message": {"raw": raw_message}}
            if request.thread_id:
                draft_request["message"]["threadId"] = request.thread_id

            result = self.service.users().drafts().create(userId="me", body=draft_request).execute()

            return result["id"]
        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            raise

    async def list_drafts(
        self, max_results: int = 10, page_token: Optional[str] = None
    ) -> DraftListResponse:
        """List draft emails.

        Args:
            max_results: Maximum number of drafts to return
            page_token: Page token for pagination

        Returns:
            DraftListResponse with drafts
        """
        try:
            query_params = {"userId": "me", "maxResults": max_results}

            if page_token:
                query_params["pageToken"] = page_token

            result = self.service.users().drafts().list(**query_params).execute()

            drafts = []
            for draft_data in result.get("drafts", []):
                # Get full draft details
                full_draft = (
                    self.service.users()
                    .drafts()
                    .get(userId="me", id=draft_data["id"], format="full")
                    .execute()
                )

                message = self._parse_message(full_draft["message"])

                draft = Draft(id=full_draft["id"], message=message)
                drafts.append(draft)

            return DraftListResponse(
                drafts=drafts,
                next_page_token=result.get("nextPageToken"),
                result_size_estimate=result.get("resultSizeEstimate"),
            )
        except Exception as e:
            logger.error(f"Error listing drafts: {e}")
            raise

    async def send_draft(self, draft_id: str) -> str:
        """Send a draft email.

        Args:
            draft_id: Draft ID to send

        Returns:
            Message ID of sent email
        """
        try:
            result = (
                self.service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
            )

            return result["id"]
        except Exception as e:
            logger.error(f"Error sending draft: {e}")
            raise

    async def get_attachment(self, message_id: str, attachment_id: str) -> AttachmentData:
        """Download an email attachment.

        Args:
            message_id: Message ID containing the attachment
            attachment_id: Attachment ID

        Returns:
            AttachmentData with downloaded content
        """
        try:
            attachment = (
                self.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )

            return AttachmentData(
                attachment_id=attachment_id,
                size=attachment.get("size", 0),
                data=attachment.get("data"),
            )
        except Exception as e:
            logger.error(f"Error getting attachment: {e}")
            raise
