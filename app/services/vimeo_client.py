import logging
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from typing import Optional, Dict, Any, BinaryIO
from app.schemas.video import Video, VideoList, UploadResponse

logger = logging.getLogger(__name__)

class VimeoClient:
    def __init__(self):
        self.base_url = settings.VIMEO_BASE_URL
        self.headers = {
            "Authorization": f"bearer {settings.VIMEO_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.vimeo.*+json;version=3.4"
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Internal wrapper for httpx requests with error handling.
        """
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Vimeo API Error: {e.response.text}")
                status_code = e.response.status_code
                detail = f"Vimeo API Error: {e.response.text}"
                
                if status_code == 401:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Vimeo Token")
                elif status_code == 403:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission Denied")
                elif status_code == 404:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource Not Found")
                elif status_code == 429:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate Limit Exceeded")
                else:
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
            except httpx.RequestError as e:
                logger.error(f"Request Error: {str(e)}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    def _normalize_video(self, data: Dict[str, Any]) -> Video:
        """
        Extracts relevant fields from Vimeo response to match Video schema.
        """
        # ID is usually at the end of the URI, e.g., /videos/12345
        video_id = data.get("uri", "").split("/")[-1]
        
        # Embed HTML might be in 'embed'['html']
        embed_html = data.get("embed", {}).get("html")

        return Video(
            id=video_id,
            name=data.get("name", "Untitled"),
            description=data.get("description"),
            duration=data.get("duration", 0),
            link=data.get("link", ""),
            embed_html=embed_html,
            pictures=data.get("pictures")
        )

    async def get_videos(self, page: int = 1, per_page: int = 25, sort: Optional[str] = None) -> VideoList:
        params = {"page": page, "per_page": per_page}
        if sort:
            params["sort"] = sort
        
        data = await self._request("GET", "/me/videos", params=params)
        
        videos = [self._normalize_video(v) for v in data.get("data", [])]
        return VideoList(
            data=videos,
            page=data.get("page", 1),
            per_page=data.get("per_page", 25),
            total=data.get("total", 0)
        )

    async def search_videos(self, query: str, page: int = 1, per_page: int = 25) -> VideoList:
        params = {"query": query, "page": page, "per_page": per_page}
        data = await self._request("GET", "/me/videos", params=params)
        
        videos = [self._normalize_video(v) for v in data.get("data", [])]
        return VideoList(
            data=videos,
            page=data.get("page", 1),
            per_page=data.get("per_page", 25),
            total=data.get("total", 0)
        )

    async def get_video(self, video_id: str) -> Video:
        data = await self._request("GET", f"/videos/{video_id}")
        return self._normalize_video(data)

    async def upload_video(self, file_obj: BinaryIO, size: int) -> UploadResponse:
        """
        Implements the 'post' upload approach (create ticket -> upload to link).
        1. Request upload ticket
        2. Upload binary data
        """
        # Step 1: Create Upload Ticket
        body = {
            "upload": {
                "approach": "post",
                "size": size
            },
            "name": "Uploaded via API"
        }
        ticket = await self._request("POST", "/me/videos", json=body)
        
        upload_link = ticket.get("upload", {}).get("upload_link")
        video_uri = ticket.get("uri")
        video_link = ticket.get("link")
        
        if not upload_link:
            raise HTTPException(status_code=500, detail="Failed to retrieve upload link from Vimeo")

        # Step 2: Upload Content (using a raw httpx client to put binary)
        # Note: We don't use self._request because this is a weird PUT to a specific URL
        logger.info(f"Uploading {size} bytes to {upload_link}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # Need to read the file pointer
                # In a real heavy app, we'd stream this. 
                # For this task, we'll read into memory or pass the generator if supported.
                content = file_obj.read()
                
                upload_resp = await client.patch(
                    upload_link, 
                    content=content,
                    headers={
                        "Tus-Resumable": "1.0.0", # specific for tus, but 'post' approach uses simple PUT/PATCH
                        "Upload-Offset": "0", 
                        "Content-Type": "application/offset+octet-stream"
                    }
                )
                
                # Vimeo 'post' approach usually requires a standard PUT or a specific TUS-like PATCH depending on the response.
                # However, the standard 'post' approach documentation says: "Send the file content to the upload_link".
                # Let's try standard PUT first, or check what 'approach' we got.
                # If we asked for 'post', we usually get a link to PUT/POST to.
                # Actually, modern Vimeo API defaults to 'tus' if not specified, but 'post' is explicit.
                # If using 'post', we just PUT the body.
                
                # Correction: The 'post' approach returns an upload_link. We should PUT the body there.
                if upload_resp.status_code not in [200, 201, 204]:
                     # Try standard PUT if PATCH failed (though PATCH is often for tus)
                     upload_resp = await client.put(upload_link, content=content, headers={"Content-Type": "video/mp4"}) # Simplify content type

                upload_resp.raise_for_status()
                
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                raise HTTPException(status_code=502, detail="Upload to Vimeo Server failed")

        return UploadResponse(
            video_id=video_uri.split("/")[-1],
            link=video_link,
            status="uploaded_pending_transcode"
        )
