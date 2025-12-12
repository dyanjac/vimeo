from fastapi import APIRouter, Depends, Query, UploadFile, File, Response
from fastapi.responses import RedirectResponse
from typing import Literal
from app.services.vimeo_client import VimeoClient
from app.schemas.video import VideoList, PlayVideoResponse, UploadResponse

router = APIRouter()

def get_vimeo_client() -> VimeoClient:
    """Dependency injection for VimeoClient"""
    return VimeoClient()

@router.get("/", response_model=VideoList)
async def list_videos(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    sort: Literal["date", "alphabetical", "duration", "last_user_action"] = Query(None),
    client: VimeoClient = Depends(get_vimeo_client)
):
    """
    List all videos from the authenticated user's account.
    """
    return await client.get_videos(page=page, per_page=per_page, sort=sort)

@router.get("/search", response_model=VideoList)
async def search_videos(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    client: VimeoClient = Depends(get_vimeo_client)
):
    """
    Search for videos in the user's account by query string.
    """
    return await client.search_videos(query=q, page=page, per_page=per_page)

@router.get("/{video_id}/play")
async def play_video(
    video_id: str,
    mode: Literal["json", "redirect"] = Query("json"),
    client: VimeoClient = Depends(get_vimeo_client)
):
    """
    Get playback information for a specific video.
    
    - **json**: Returns the video link and embed code.
    - **redirect**: Redirects (302) to the video link.
    """
    video = await client.get_video(video_id)
    
    if mode == "redirect":
        return RedirectResponse(url=str(video.link))
    else:
        return PlayVideoResponse(link=video.link, embed_html=video.embed_html)

@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    client: VimeoClient = Depends(get_vimeo_client)
):
    """
    Upload a video file to Vimeo.
    Uses the 'post' approach:
    1. Gets an upload ticket.
    2. Streams the file content to the upload link.
    """
    # Calculate size or read into memory to get size
    # For robust handling of large files, we'd need a more streaming-friendly approach 
    # but UploadFile.file matches the BinaryIO interface needed.
    # We need the size though.
    
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    return await client.upload_video(file.file, size)
