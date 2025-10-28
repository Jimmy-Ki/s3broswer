# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a macOS-style S3 client web application built with Flask that provides a Finder-like interface for managing S3-compatible storage services (AWS S3, Alibaba Cloud OSS, Tencent Cloud COS, MinIO, etc.). The application supports multiple S3 server configurations and provides file management capabilities through a web interface.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Standard run
python app.py

# Development mode with auto-reload
export FLASK_ENV=development
python app.py

# The app runs on http://localhost:8080 (not 5000)
```

## Architecture

### Core Components

1. **app.py** - Main Flask application with API endpoints and file preview functionality
2. **s3_client.py** - S3ClientManager class that wraps boto3 operations for S3-compatible services
3. **config.py** - ConfigManager class for handling local S3 server configurations stored in JSON
4. **s3_config.json** - Local storage for S3 server credentials and configurations (created automatically)

### Key Architecture Patterns

- **Multi-server support**: Each S3 server configuration is stored locally and can be switched between dynamically
- **Client caching**: S3 clients are cached in memory to avoid re-creating connections
- **File preview system**: Supports multiple file types (images, text, PDF, CSV, SQLite databases) with temporary file handling
- **Session management**: Uses filesystem-based sessions for state management

### API Structure

- `GET/POST /api/servers` - Manage S3 server configurations
- `GET /api/servers/{id}/buckets` - List buckets for a server
- `GET /api/servers/{id}/objects` - List objects in a bucket with prefix support
- `POST /api/servers/{id}/upload` - Upload files with multipart form data
- `GET /api/servers/{id}/download` - Download files as attachments
- `DELETE /api/servers/{id}/delete` - Delete files/folders (batch operation supported)
- `POST /api/servers/{id}/folders` - Create folders
- `GET /api/servers/{id}/preview` - Preview file contents (multiple formats supported)

### File Management Features

- **Upload**: Drag-and-drop or click to select files, max 100MB
- **Download**: Single or batch downloads with proper content-disposition headers
- **Preview**: In-browser preview for images, text files, PDFs, CSV, SQLite databases
- **Delete**: Batch delete with support for both files and folders
- **Navigation**: Folder-based navigation with breadcrumb support

## Configuration

The application stores S3 server configurations in `s3_config.json` with the following structure:
- Server name, access keys, endpoint URL, region
- Configurations are local-only and not exposed to the internet
- Multiple server configurations supported

## Frontend

- Uses Bootstrap 5 with custom macOS Finder-style CSS (`static/css/finder.css`)
- Responsive design with mobile support
- Features: grid/list view toggle, keyboard shortcuts, right-click context menus
- Templates in `templates/` using Jinja2 templating

## Security Notes

- S3 credentials are stored locally in JSON format
- Temporary files are cleaned up automatically after uploads/downloads
- File uploads are limited to 100MB
- Session-based authentication for the web interface
- Access keys are only stored in memory, not logged

## Development Tips

- When adding new S3-compatible services, test with the service's endpoint URL format
- File preview functionality can be extended by modifying `process_file_preview()` in app.py
- New API endpoints should follow the existing pattern with proper error handling
- The application uses filesystem sessions, so the `flask_session/` directory must exist