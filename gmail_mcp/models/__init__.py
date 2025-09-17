"""Pydantic models for Gmail MCP server."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class LabelType(str, Enum):
    """Gmail label types."""
    SYSTEM = "system"
    USER = "user"


class MessageFormat(str, Enum):
    """Gmail message format types."""
    MINIMAL = "minimal"
    FULL = "full"
    RAW = "raw"
    METADATA = "metadata"


class ThreadFormat(str, Enum):
    """Gmail thread format types."""
    MINIMAL = "minimal"
    FULL = "full"
    METADATA = "metadata"


class AttachmentData(BaseModel):
    """Gmail attachment data model."""
    model_config = ConfigDict(extra="forbid")
    
    attachment_id: str = Field(..., description="Attachment ID")
    size: int = Field(..., description="Attachment size in bytes")
    data: Optional[str] = Field(None, description="Base64 encoded attachment data")


class MessagePart(BaseModel):
    """Gmail message part model."""
    model_config = ConfigDict(extra="forbid")
    
    part_id: Optional[str] = Field(None, description="Part ID")
    mime_type: str = Field(..., description="MIME type")
    filename: Optional[str] = Field(None, description="Filename for attachments")
    headers: List[Dict[str, str]] = Field(default_factory=list, description="Message headers")
    body: Optional[Dict[str, Any]] = Field(None, description="Message body")
    parts: Optional[List["MessagePart"]] = Field(None, description="Sub-parts")


class MessageHeader(BaseModel):
    """Gmail message header model."""
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Header name")
    value: str = Field(..., description="Header value")


class Label(BaseModel):
    """Gmail label model."""
    model_config = ConfigDict(extra="forbid")
    
    id: str = Field(..., description="Label ID")
    name: str = Field(..., description="Label name")
    type: LabelType = Field(..., description="Label type")
    message_list_visibility: Optional[str] = Field(None, description="Message list visibility")
    label_list_visibility: Optional[str] = Field(None, description="Label list visibility")
    messages_total: Optional[int] = Field(None, description="Total messages with this label")
    messages_unread: Optional[int] = Field(None, description="Unread messages with this label")
    threads_total: Optional[int] = Field(None, description="Total threads with this label")
    threads_unread: Optional[int] = Field(None, description="Unread threads with this label")


class Message(BaseModel):
    """Gmail message model."""
    model_config = ConfigDict(extra="forbid")
    
    id: str = Field(..., description="Message ID")
    thread_id: str = Field(..., description="Thread ID")
    label_ids: List[str] = Field(default_factory=list, description="Label IDs")
    snippet: Optional[str] = Field(None, description="Message snippet")
    history_id: Optional[str] = Field(None, description="History ID")
    internal_date: Optional[datetime] = Field(None, description="Internal date")
    payload: Optional[MessagePart] = Field(None, description="Message payload")
    size_estimate: Optional[int] = Field(None, description="Size estimate")
    raw: Optional[str] = Field(None, description="Raw message data")
    
    # Computed fields
    subject: Optional[str] = Field(None, description="Message subject")
    sender: Optional[str] = Field(None, description="Message sender")
    recipient: Optional[str] = Field(None, description="Message recipient")
    date: Optional[datetime] = Field(None, description="Message date")
    body_text: Optional[str] = Field(None, description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    attachments: List[AttachmentData] = Field(default_factory=list, description="Attachments")


class Thread(BaseModel):
    """Gmail thread model."""
    model_config = ConfigDict(extra="forbid")
    
    id: str = Field(..., description="Thread ID")
    snippet: Optional[str] = Field(None, description="Thread snippet")
    history_id: Optional[str] = Field(None, description="History ID")
    messages: List[Message] = Field(default_factory=list, description="Messages in thread")


class Draft(BaseModel):
    """Gmail draft model."""
    model_config = ConfigDict(extra="forbid")
    
    id: str = Field(..., description="Draft ID")
    message: Message = Field(..., description="Draft message")


class Profile(BaseModel):
    """Gmail profile model."""
    model_config = ConfigDict(extra="forbid")
    
    email_address: str = Field(..., description="Email address")
    messages_total: int = Field(..., description="Total messages")
    threads_total: int = Field(..., description="Total threads")
    history_id: str = Field(..., description="History ID")


# Request/Response Models

class SendEmailRequest(BaseModel):
    """Request model for sending emails."""
    model_config = ConfigDict(extra="forbid")
    
    to: List[str] = Field(..., description="Recipient email addresses")
    cc: Optional[List[str]] = Field(None, description="CC recipients")
    bcc: Optional[List[str]] = Field(None, description="BCC recipients")
    subject: str = Field(..., description="Email subject")
    body_text: Optional[str] = Field(None, description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    thread_id: Optional[str] = Field(None, description="Thread ID for replies")
    in_reply_to: Optional[str] = Field(None, description="Message ID being replied to")
    attachments: Optional[List[str]] = Field(None, description="Attachment file paths")


class SearchEmailsRequest(BaseModel):
    """Request model for searching emails."""
    model_config = ConfigDict(extra="forbid")
    
    query: str = Field(..., description="Gmail search query")
    max_results: int = Field(default=10, ge=1, le=500, description="Maximum results")
    page_token: Optional[str] = Field(None, description="Page token for pagination")
    include_spam_trash: bool = Field(default=False, description="Include spam and trash")


class EmailListRequest(BaseModel):
    """Request model for listing emails."""
    model_config = ConfigDict(extra="forbid")
    
    label_ids: Optional[List[str]] = Field(None, description="Filter by label IDs")
    q: Optional[str] = Field(None, description="Search query")
    max_results: int = Field(default=10, ge=1, le=500, description="Maximum results")
    page_token: Optional[str] = Field(None, description="Page token for pagination")
    include_spam_trash: bool = Field(default=False, description="Include spam and trash")


class ModifyLabelsRequest(BaseModel):
    """Request model for modifying message labels."""
    model_config = ConfigDict(extra="forbid")
    
    add_label_ids: Optional[List[str]] = Field(None, description="Label IDs to add")
    remove_label_ids: Optional[List[str]] = Field(None, description="Label IDs to remove")


class CreateLabelRequest(BaseModel):
    """Request model for creating labels."""
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Label name")
    message_list_visibility: str = Field(default="show", description="Message list visibility")
    label_list_visibility: str = Field(default="labelShow", description="Label list visibility")


class ForwardEmailRequest(BaseModel):
    """Request model for forwarding emails."""
    model_config = ConfigDict(extra="forbid")
    
    to: List[str] = Field(..., description="Recipient email addresses")
    cc: Optional[List[str]] = Field(None, description="CC recipients")
    bcc: Optional[List[str]] = Field(None, description="BCC recipients")
    additional_message: Optional[str] = Field(None, description="Additional message to include")


class CreateDraftRequest(BaseModel):
    """Request model for creating drafts."""
    model_config = ConfigDict(extra="forbid")
    
    to: List[str] = Field(..., description="Recipient email addresses")
    cc: Optional[List[str]] = Field(None, description="CC recipients")
    bcc: Optional[List[str]] = Field(None, description="BCC recipients")
    subject: str = Field(..., description="Email subject")
    body_text: Optional[str] = Field(None, description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    thread_id: Optional[str] = Field(None, description="Thread ID for replies")
    in_reply_to: Optional[str] = Field(None, description="Message ID being replied to")


class ThreadListRequest(BaseModel):
    """Request model for listing threads."""
    model_config = ConfigDict(extra="forbid")
    
    label_ids: Optional[List[str]] = Field(None, description="Filter by label IDs")
    q: Optional[str] = Field(None, description="Search query")
    max_results: int = Field(default=10, ge=1, le=500, description="Maximum results")
    page_token: Optional[str] = Field(None, description="Page token for pagination")
    include_spam_trash: bool = Field(default=False, description="Include spam and trash")


# Response Models

class ApiResponse(BaseModel):
    """Base API response model."""
    model_config = ConfigDict(extra="forbid")
    
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")


class EmailListResponse(BaseModel):
    """Response model for email listing."""
    model_config = ConfigDict(extra="forbid")
    
    messages: List[Message] = Field(..., description="List of messages")
    next_page_token: Optional[str] = Field(None, description="Next page token")
    result_size_estimate: Optional[int] = Field(None, description="Estimated result size")


class ThreadListResponse(BaseModel):
    """Response model for thread listing."""
    model_config = ConfigDict(extra="forbid")
    
    threads: List[Thread] = Field(..., description="List of threads")
    next_page_token: Optional[str] = Field(None, description="Next page token")
    result_size_estimate: Optional[int] = Field(None, description="Estimated result size")


class LabelListResponse(BaseModel):
    """Response model for label listing."""
    model_config = ConfigDict(extra="forbid")
    
    labels: List[Label] = Field(..., description="List of labels")


class DraftListResponse(BaseModel):
    """Response model for draft listing."""
    model_config = ConfigDict(extra="forbid")
    
    drafts: List[Draft] = Field(..., description="List of drafts")
    next_page_token: Optional[str] = Field(None, description="Next page token")
    result_size_estimate: Optional[int] = Field(None, description="Estimated result size")


# Fix forward references
MessagePart.model_rebuild()