import pytest
from app.schemas.video import Video, VideoList, UploadResponse

@pytest.mark.asyncio
async def test_list_videos(client, mock_vimeo_client):
    # Setup mock
    mock_video = Video(
        id="123", 
        name="Test Video", 
        duration=60, 
        link="https://vimeo.com/123",
        embed_html=None,
        pictures=None
    )
    mock_response = VideoList(data=[mock_video], page=1, per_page=25, total=1)
    mock_vimeo_client.get_videos.return_value = mock_response

    response = await client.get("/v1/videos")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["id"] == "123"
    assert data["data"][0]["name"] == "Test Video"

@pytest.mark.asyncio
async def test_play_video_redirect(client, mock_vimeo_client):
    mock_video = Video(
        id="123", 
        name="Test Video", 
        duration=60, 
        link="https://vimeo.com/123", 
        embed_html=None
    )
    mock_vimeo_client.get_video.return_value = mock_video

    response = await client.get("/v1/videos/123/play?mode=redirect", follow_redirects=False)
    
    assert response.status_code == 302
    assert response.headers["location"] == "https://vimeo.com/123"

@pytest.mark.asyncio
async def test_upload_video(client, mock_vimeo_client):
    mock_upload = UploadResponse(
        video_id="new123",
        link="https://vimeo.com/new123",
        status="complete"
    )
    mock_vimeo_client.upload_video.return_value = mock_upload

    # Create dummy file
    files = {'file': ('test.mp4', b'fake content', 'video/mp4')}
    response = await client.post("/v1/videos/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "new123"
