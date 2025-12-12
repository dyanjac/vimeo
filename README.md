# FastAPI Vimeo API Wrapper

A production-ready FastAPI application to act as a proxy/wrapper for the Vimeo API, providing endpoints to list, search, play, and upload videos.

## Features
- **List Videos**: Pagination support.
- **Search Videos**: Query-based search details.
- **Play Video**: Retrieve direct links or use redirects.
- **Upload Video**: Streamlined upload flow using Vimeo's API.
- **Async**: Built with `httpx` for high-performance async I/O.
- **Robustness**: Proper error handling and logging.

## Requirements
- Python 3.11+
- [Vimeo Developer Account](https://developer.vimeo.com/)

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd magnetic-rocket
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Copy `.env.example` to `.env` and fill in your values.
   ```bash
   cp .env .env
   ```
   *   `VIMEO_ACCESS_TOKEN`: Create an app on Vimeo Developer Portal. Generate a **Personal Access Token** with at least `private`, `create`, `edit` and `upload` scopes if you plan to upload.

## Running the Application

Start the server using `uvicorn`:
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.

## API Usage

### 1. List Videos
```bash
curl "http://localhost:8000/v1/videos?page=1&per_page=10"
```

### 2. Search Videos
```bash
curl "http://localhost:8000/v1/videos/search?q=tutorial"
```

### 3. Play Video
**Get JSON metadata:**
```bash
curl "http://localhost:8000/v1/videos/12345/play?mode=json"
```
**Redirect to playback source:**
```bash
curl -L -v "http://localhost:8000/v1/videos/12345/play?mode=redirect"
```

### 4. Upload Video
```bash
curl -X POST "http://localhost:8000/v1/videos/upload" \
  -F "file=@/path/to/myvideo.mp4"
```

## Running Tests
Run the test suite using `pytest`:
```bash
pytest tests/
```

## Troubleshooting & Permissions

### 401 Unauthorized
- **Cause**: Invalid or expired `VIMEO_ACCESS_TOKEN`.
- **Fix**: Regenerate token in Vimeo Developer Dashboard.

### 403 Forbidden
- **Cause**: Token lacks necessary scopes (especially for Uploads).
- **Fix**: Ensure your token has `private` (for listing own videos) and `upload` (for uploading) scopes.

### 502 Bad Gateway / Upload Issues
- **Cause**: Vimeo API errors or network issues during large uploads.
- **Fix**: Check `app.log` or console output for detailed Vimeo error messages. Ensure your account has storage quota remaining.

## Notes on Uploads
This project uses the Vimeo `post` approach (Upload Ticket -> Direct File Stream).
- For very large files (GBs), a Resumable (`tus`) approach is recommended but adds significant complexity.
- The current implementation buffers the file pointer or streams it depending on the client; for production with huge files, ensure your reverse proxy (nginx) allows large bodies.
