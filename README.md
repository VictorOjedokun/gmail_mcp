# Gmail MCP Server

A comprehensive Model Context Protocol (MCP) server for Gmail operations with 21 production-ready tools.

## Features

### 📧 Complete Gmail Integration
- **21 MCP Tools** covering all Gmail operations
- **OAuth 2.0 Authentication** with token validation
- **Production-Ready** error handling and logging
- **Type Safety** with comprehensive Pydantic models

### 🛠️ Tool Categories

#### Email Reading (5 tools)
- `get_emails` - List emails with filtering options
- `get_email_by_id` - Get specific email by ID
- `search_emails` - Search emails with Gmail query syntax
- `get_labels` - List all Gmail labels
- `get_profile` - Get Gmail profile information

#### Email Management (9 tools)
- `send_email` - Send new emails
- `reply_to_email` - Reply to existing emails
- `mark_as_read` / `mark_as_unread` - Manage read status
- `archive_email` - Archive emails
- `delete_email` - Delete emails
- `add_label` / `remove_label` - Manage email labels
- `create_label` - Create new labels

#### Advanced Features (7 tools)
- `forward_email` - Forward emails with additional message
- `move_to_folder` - Move emails between folders
- `get_threads` - List conversation threads
- `create_draft` - Create draft emails
- `get_drafts` - List draft emails
- `send_draft` - Send draft emails
- `get_attachments` - Download email attachments

## 🏗️ Architecture

This project implements a **separation of concerns** architecture with two main components:

1. **Gmail MCP Server** (`main.py`) - Handles Gmail operations with bearer token authentication
2. **OAuth Server** (separate service) - Manages Google OAuth 2.0 flow and token validation

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Client App        │    │   OAuth Server       │    │  Gmail MCP      │
│                     │────│  (Port 8000)         │    │  Server         │
│ Gets token from     │    │                      │    │  (Port 8001)    │
│ OAuth, passes to    │    │ - Google OAuth flow  │    │                 │
│ Gmail MCP           │    │ - Token management   │    │ - Gmail tools   │
│                     │    │ - Token validation   │    │ - Requires token│
└─────────────────────┘    └──────────────────────┘    └─────────────────┘
```

## Installation

```bash
# Clone and install
git clone <repository>
cd gmail_mcp
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your Google OAuth credentials
```

## Configuration

```bash
# Required environment variables
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
OAUTH_SERVER_URL=http://localhost:8000  # Your OAuth server URL
MCP_SERVER_NAME=gmail_mcp_server
LOG_LEVEL=INFO
```

## Usage

### Start the MCP Server
```bash
uv run python main.py
```

### OAuth Flow
1. Set up a standalone OAuth server (separate from this MCP server)
2. Users authenticate via OAuth server
3. MCP server validates tokens via OAuth server
4. All Gmail operations use validated credentials

### Example MCP Client Usage
```python
# The MCP client can call any of the 21 tools:
await mcp_client.call_tool("get_emails", {
    "max_results": 10,
    "label_ids": ["INBOX"],
    "include_spam_trash": False
})

await mcp_client.call_tool("send_email", {
    "to": ["recipient@example.com"],
    "subject": "Hello from MCP",
    "body_text": "This email was sent via MCP!"
})

await mcp_client.call_tool("forward_email", {
    "email_id": "msg_123",
    "to": ["forward@example.com"],
    "additional_message": "FYI - this might interest you"
})
```

## Project Structure

```
gmail_mcp/
├── core/          # Configuration and settings
├── models/        # Pydantic data models
├── auth/          # OAuth token validation
├── services/      # Gmail API integration
└── tools/         # MCP tool implementations
    ├── reading.py    # Email reading tools
    ├── management.py # Email management tools
    └── advanced.py   # Advanced Gmail features
```

## Google API Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Gmail API
3. Create OAuth 2.0 credentials
4. Add authorized redirect URIs for your OAuth server
5. Download credentials and set environment variables

## OAuth Server Integration

This MCP server expects a separate OAuth server for authentication:

- **OAuth Server**: Handles Google OAuth flow and token management
- **MCP Server**: Validates tokens and provides Gmail tools
- **Token Flow**: MCP server calls OAuth server to validate tokens

## Development

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run python test_enhanced.py

# Type checking
uv run mypy gmail_mcp

# Code formatting
uv run black gmail_mcp
```

## Production Deployment

1. **OAuth Server**: Deploy standalone OAuth service
2. **MCP Server**: Deploy this Gmail MCP server
3. **Configuration**: Set proper OAuth server URL
4. **Security**: Use HTTPS and secure token validation
5. **Monitoring**: Enable logging and error tracking

## Error Handling

- **Token Validation**: Automatic token validation with clear error messages
- **API Errors**: Gmail API errors are caught and returned as structured responses
- **Rate Limiting**: Respects Gmail API rate limits
- **Logging**: Comprehensive logging for debugging and monitoring

## Security

- **OAuth 2.0**: Industry-standard authentication
- **Token Validation**: Server-side token verification
- **Scope Management**: Minimal required Gmail scopes
- **No Token Storage**: Tokens validated per-request, not stored

## License

MIT License - see LICENSE file for details.