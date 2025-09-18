# Gmail Message Formats

This document explains the different message formats available in the Gmail MCP server and what data each format returns.

## Message Format Types

### MINIMAL
**Best for:** Super fast listing when you only need basic IDs
**Performance:** ⚡ Fastest
**Data returned:**
- `id`: Message ID
- `threadId`: Thread ID  
- `labelIds`: Array of label IDs applied to the message
- `snippet`: Short preview text (automatically generated)
- `historyId`: History ID for change tracking

**Use cases:**
- Basic email enumeration
- When you only need message IDs
- Extremely performance-sensitive operations

### COMPACT (Default) ⭐
**Best for:** Practical email browsing with content preview
**Performance:** 🚀 Fast
**Data returned:**
- All MINIMAL data +
- `subject`: Email subject line
- `sender`: From address
- `recipient`: To address  
- `date`: Parsed date
- `body_text`: Plain text body content
- `sizeEstimate`: Estimated message size

**Use cases:**
- Email listing with content preview
- Search results with readable content
- Most common use case - shows you what you need to know
- Reading emails without heavy attachments/HTML

### FULL
**Best for:** Reading complete email content
**Performance:** 🐌 Slower (more data)
**Data returned:**
- All COMPACT data +
- `payload`: Complete message structure including:
  - `headers`: All email headers (From, To, Subject, Date, etc.)
  - `body`: Message body parts (text, HTML)
  - `parts`: Multipart message structure
  - `attachments`: Attachment metadata and data
- `internalDate`: Gmail's internal timestamp
- Full parsed content:
  - `body_html`: HTML body
  - `attachments`: Processed attachment list

**Use cases:**
- Reading email content with attachments
- Displaying full email details with formatting
- Processing attachments
- Reply/Forward operations

### METADATA
**Best for:** Headers and labels without body content
**Performance:** 🚀 Medium
**Data returned:**
- All MINIMAL data +
- `payload.headers`: All email headers
- `sizeEstimate`: Message size estimate
- Parsed headers:
  - `subject`: Email subject
  - `sender`: From address
  - `recipient`: To address
  - `date`: Parsed date
- NO body content or attachments

**Use cases:**
- Email analysis without content
- Header inspection
- Filtering by header values
- When body content is not needed

### RAW
**Best for:** Original RFC2822 message data
**Performance:** 🚀 Medium
**Data returned:**
- All MINIMAL data +
- `raw`: Base64-encoded RFC2822 message
- Limited parsed data (mainly IDs and basic metadata)

**Use cases:**
- Email migration
- Advanced email processing
- Backup/archival
- Custom parsing requirements


## Performance Recommendations

1. **Use MINIMAL for browsing**: When listing or searching emails, use MINIMAL format for faster response times
2. **Use COMPACT for LLM**: When getting to extract data from emails with LLMs, use CCOMPACT format for a balance between faster and smaller context.
3. **Use FULL for reading**: When displaying email content to users, use FULL format
4. **Use METADATA for analysis**: When you need headers but not body content
5. **Use RAW for advanced needs**: Only when you need the original message format
