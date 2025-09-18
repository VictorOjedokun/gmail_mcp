# Gmail MCP Server

A comprehensive Model Context Protocol (MCP) server for Gmail operations with **25 production-ready tools** and streamable HTTP transport.

## 🚀 Quick Start

### Prerequisites
```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation
```bash
# Clone and install dependencies
git clone <repository>
cd gmail_mcp
uv sync
```

### Development Setup
```bash
# Copy environment template
cp .env.example .env
# Edit .env with your configuration (see Configuration section)

# Start development server (auto-reload)
uv run python start_server.py
# OR manually with custom port
uvicorn main:app --reload --port 8002
```


## Features

### Complete Gmail Integration
- **25 MCP Tools** covering all Gmail operations
- **OAuth 2.0 Authentication** with Google token validation
- **Type Safety** with comprehensive Pydantic models


## Tools available (25 Total)

- `gmail_get_emails` - List emails with filtering, pagination, and date ranges
- `gmail_get_my_sent_emails` - Get sent emails with date filtering
- `gmail_get_email_by_id` - Get specific email by ID with format options
- `gmail_search_emails` - Advanced search with Gmail query syntax and date ranges
- `gmail_get_labels` - List all Gmail labels and their properties
- `gmail_get_profile` - Get Gmail profile and account information
- `gmail_send_email` - Send new emails with attachments and formatting
- `gmail_reply_to_email` - Reply to emails with options for reply-all
- `gmail_mark_as_read` / `gmail_mark_as_unread` - Manage read status
- `gmail_archive_email` / `gmail_unarchive_email` - Archive management
- `gmail_delete_email` - Delete emails (move to trash)
- `gmail_add_label` / `gmail_remove_label` - Manage email labels
- `gmail_create_label` - Create new custom labels
- `gmail_forward_email` - Forward emails with additional message
- `gmail_move_to_folder` - Move emails between folders/labels
- `gmail_get_threads` - List conversation threads with date filtering
- `gmail_get_thread_by_id` - Get specific thread by ID
- `gmail_create_draft` - Create draft emails
- `gmail_get_drafts` - List draft emails with date filtering
- `gmail_get_draft_by_id` - Get specific draft by ID  
- `gmail_send_draft` - Send existing drafts
- `gmail_get_attachments` - Download email attachments

## Configuration

### Environment Variables (.env)
```bash
# Server Configuration
SERVER_HOST=0.0.0.0                    # Server bind address
SERVER_PORT=8001                       # Server port
SERVER_URL=http://localhost:8001       # This server's URL for OAuth validation
DEBUG=false                            # Enable debug mode

# Transport Configuration
TRANSPORT_TYPE=streamble_http           # streamble_http or sse
MCP_SERVER_NAME=gmail_mcp_server       # MCP server identifier

# Logging
LOG_LEVEL=INFO                         # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### OAuth Scopes
The server requires these Gmail scopes:
- `gmail.readonly` - Read emails and labels
- `gmail.send` - Send emails  
- `gmail.modify` - Modify emails (archive, label, etc.)
- `gmail.compose` - Create drafts
- `gmail.labels` - Manage labels

## Message Formats (For when Getting emails)

The server supports 5 message formats for optimal performance:

### **COMPACT (Default)** 
- **Best for**: General email browsing and AI processing
- **Contains**: Headers + plain text body + metadata
- **Use case**: Most common operations

### **MINIMAL**
- **Best for**: Listing and enumeration
- **Contains**: ID, labels, snippet only
- **Use case**: High-volume operations

### **FULL**
- **Best for**: Complete email reading
- **Contains**: All data including HTML, attachments
- **Use case**: Display full emails

### **METADATA**
- **Best for**: Header analysis
- **Contains**: All headers, no body content
- **Use case**: Email analysis without content

### **RAW**
- **Best for**: Email processing
- **Contains**: Original RFC2822 format
- **Use case**: Migration, backup

## Date Range Filtering

Most tools support flexible date filtering:

### **Absolute Dates**
```python
# YYYY-MM-DD or YYYY/MM/DD format
after_date="2024-01-01"
before_date="2024-12-31"
```

### **Relative Timeframes**
```python
# Days, weeks, months, years
newer_than="1d"    # Last day
older_than="6m"    # Older than 6 months
```

### **Examples**
```python
# Get recent important emails
gmail_get_emails(label_ids=["IMPORTANT"], newer_than="1w", format="COMPACT")

# Search emails in date range
gmail_search_emails(query="project", after_date="2024-06-01", before_date="2024-06-30")
```

## Architecture

### **MCP Server Design**
- **Transport**: Streamable HTTP (default) or SSE
- **Authentication**: Google OAuth 2.0 with token validation
- **Format**: JSON-based MCP protocol
- **Streaming**: Real-time response streaming for large operations

### **OAuth Flow**
```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   MCP Client        │    │   Google OAuth       │    │  Gmail MCP      │
│                     │    │   (accounts.google)  │    │  Server         │
│ 1. Request with     │────│ 2. Validates token   │────│ 3. Gmail API    │
│    Bearer token     │    │    Returns user info │    │    operations   │
│                     │    │                      │    │                 │
└─────────────────────┘    └──────────────────────┘    └─────────────────┘
```



## API Reference

### **Authentication**
All endpoints require a valid Google OAuth token:
```http
Authorization: Bearer <google_oauth_token>
```



## Development

### **Project Setup**
```bash
# Install dependencies
uv sync

# Setup environment
cp .env.example .env
# Edit .env file with your configuration

# Run tests
uv run python mail_test_main.py

# Start development server with auto-reload
uv run python start_server.py
```

### **Development Commands**
```bash
# Development server (auto-reload)
uv run python start_server.py

# Manual development with custom port
uvicorn main:app --reload --port 8002

# Production server
uvicorn main:app --host 0.0.0.0 --port 8001

# Run interactive tests
uv run python mail_test_main.py
```

### **Testing Tools**
The project includes `service_example/service_functions_test.py` - an interactive test suite:
- Tests all 25 Gmail Service functions

### **Gmail OAuth Scopes**
The server automatically configures these required scopes:
```python
REQUIRED_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send", 
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.labels"
]
```

## 🔐 Google OAuth Setup

1. **Google Cloud Console**
   - Create project at [console.cloud.google.com](https://console.cloud.google.com)
   - Enable Gmail API
   - Create OAuth 2.0 credentials

2. **OAuth Configuration**
   - Add authorized origins: `http://localhost:8001`
   - Add redirect URIs as needed for your OAuth flow
   - Download credentials (not stored in this server)

3. **Token Validation**
   - This server validates tokens with Google's `accounts.google.com` - For getting an access token for quick test, check ```service_example/get_access_token.py```
   - No credential storage - tokens validated per request


## 📝 License

MIT License - see LICENSE file for details.
