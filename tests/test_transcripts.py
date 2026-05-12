from pathlib import Path
import subprocess

from app.services.transcripts import (
    TranscriptSegment,
    clean_caption_text,
    download_youtube_captions,
    filter_segments,
    parse_vtt,
)


def test_clean_caption_text_removes_vtt_markup():
    assert clean_caption_text("안녕<00:00:01.000><c>하세요</c>&amp; 반가워요") == "안녕하세요& 반가워요"


def test_parse_vtt_reads_caption_segments(tmp_path: Path):
    path = tmp_path / "captions.ko.vtt"
    path.write_text(
        """WEBVTT
Kind: captions
Language: ko

00:00:00.000 --> 00:00:02.500
안녕하세요.

00:00:02.500 --> 00:00:05.000
오늘은 한국어를 공부해요.
""",
        encoding="utf-8",
    )

    segments = parse_vtt(path)

    assert segments == [
        TranscriptSegment(start_sec=0.0, end_sec=2.5, text="안녕하세요."),
        TranscriptSegment(start_sec=2.5, end_sec=5.0, text="오늘은 한국어를 공부해요."),
    ]


def test_filter_segments_keeps_overlapping_segments():
    segments = [
        TranscriptSegment(start_sec=0, end_sec=2, text="one"),
        TranscriptSegment(start_sec=2, end_sec=4, text="two"),
        TranscriptSegment(start_sec=4, end_sec=6, text="three"),
    ]

    assert filter_segments(segments, start_sec=1, end_sec=5) == segments
    assert filter_segments(segments, start_sec=2.1, end_sec=3.9) == [segments[1]]


def test_download_youtube_captions_uses_runner_and_parses_vtt(tmp_path: Path):
    def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
        assert args[0] == "yt-dlp"
        (tmp_path / "captions.ko.vtt").write_text(
            """WEBVTT

00:00:00.000 --> 00:00:05.000
안녕하세요. 오늘은 서울의 길거리 음식을 함께 즐겨볼게요.

00:00:05.000 --> 00:00:10.000
이 시장은 현지인도 자주 와서 맛있는 음식 가게로 가득해요.
""",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    transcript = download_youtube_captions(
        "https://youtu.be/abc123XYZ00",
        tmp_path,
        lang="ko",
        start_sec=0,
        end_sec=10,
        allow_auto=True,
        runner=runner,
    )

    assert transcript is not None
    assert transcript.source == "youtube_auto_caption"
    assert "길거리 음식" in transcript.text
    assert len(transcript.segments) == 2
