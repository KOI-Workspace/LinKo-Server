from pathlib import Path
from unittest.mock import patch, MagicMock
from app.services.transcripts import (
    TranscriptSegment,
    download_youtube_captions,
    filter_segments,
)

def test_filter_segments_keeps_overlapping_segments():
    segments = [
        TranscriptSegment(start_sec=0, end_sec=2, text="one"),
        TranscriptSegment(start_sec=2, end_sec=4, text="two"),
        TranscriptSegment(start_sec=4, end_sec=6, text="three"),
    ]

    assert filter_segments(segments, start_sec=1, end_sec=5) == segments
    assert filter_segments(segments, start_sec=2.1, end_sec=3.9) == [segments[1]]


@patch("app.services.transcripts.httpx.get")
@patch("app.services.transcripts.get_settings")
def test_download_youtube_captions_success(mock_get_settings, mock_get, tmp_path: Path):
    mock_settings = MagicMock()
    mock_settings.supadata_api_key = "test-key"
    mock_get_settings.return_value = mock_settings

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [
            {"text": "안녕하세요.", "offset": 0, "duration": 5000, "lang": "ko"},
            {"text": "서울의 길거리 음식입니다.", "offset": 5000, "duration": 5000, "lang": "ko"},
        ],
        "lang": "ko"
    }
    mock_get.return_value = mock_response

    transcript = download_youtube_captions(
        "https://youtu.be/abc123XYZ00",
        tmp_path,
        lang="ko",
        start_sec=0,
        end_sec=10,
        allow_auto=True
    )

    assert transcript is not None
    assert transcript.source == "youtube_caption"
    assert "길거리 음식" in transcript.text
    assert len(transcript.segments) == 2
    assert transcript.segments[0].start_sec == 0.0
    assert transcript.segments[1].end_sec == 10.0
    assert transcript.lang == "ko"


@patch("app.services.transcripts.httpx.get")
@patch("app.services.transcripts.get_settings")
def test_download_youtube_captions_rejects_supadata_language_fallback(
    mock_get_settings,
    mock_get,
    tmp_path: Path,
):
    mock_settings = MagicMock()
    mock_settings.supadata_api_key = "test-key"
    mock_get_settings.return_value = mock_settings

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [
            {"text": "안녕하세요.", "offset": 0, "duration": 5000, "lang": "ko"},
        ],
        "lang": "ko",
        "availableLangs": ["ko"],
    }
    mock_get.return_value = mock_response

    transcript = download_youtube_captions(
        "https://youtu.be/abc123XYZ00",
        tmp_path,
        lang="en",
        start_sec=0,
        end_sec=10,
        allow_auto=True,
    )

    assert transcript is None
