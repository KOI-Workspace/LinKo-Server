from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal
import html
import re
import subprocess


@dataclass(frozen=True)
class TranscriptSegment:
    start_sec: float
    end_sec: float
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    source: Literal["youtube_caption", "youtube_auto_caption"]
    text: str
    segments: list[TranscriptSegment]


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]

TIMESTAMP_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})[.,](?P<ms>\d{3})"
)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def timestamp_to_seconds(value: str) -> float:
    match = TIMESTAMP_RE.search(value)
    if match is None:
        raise ValueError(f"Invalid timestamp: {value}")
    return (
        int(match.group("h")) * 3600
        + int(match.group("m")) * 60
        + int(match.group("s"))
        + int(match.group("ms")) / 1000
    )


def clean_caption_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_vtt(path: Path) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    current_range: tuple[float, float] | None = None
    text_lines: list[str] = []

    def flush() -> None:
        nonlocal current_range, text_lines
        if current_range and text_lines:
            text = clean_caption_text(" ".join(text_lines))
            if text:
                segments.append(TranscriptSegment(current_range[0], current_range[1], text))
        current_range = None
        text_lines = []

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if "-->" in line:
            flush()
            start_raw, end_raw = [part.strip() for part in line.split("-->", 1)]
            end_raw = end_raw.split(" ", 1)[0]
            current_range = (timestamp_to_seconds(start_raw), timestamp_to_seconds(end_raw))
            continue
        if line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if current_range:
            text_lines.append(line)
    flush()
    return segments


def filter_segments(
    segments: list[TranscriptSegment],
    start_sec: float,
    end_sec: float,
) -> list[TranscriptSegment]:
    return [
        item
        for item in segments
        if item.end_sec > start_sec and item.start_sec < end_sec
    ]


def download_youtube_captions(
    url: str,
    output_dir: Path,
    lang: str,
    start_sec: int,
    end_sec: int,
    allow_auto: bool = True,
    runner: CommandRunner = run_command,
) -> TranscriptResult | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "captions.%(ext)s")
    args = [
        "yt-dlp",
        "--skip-download",
        "--sub-lang",
        lang,
        "--write-sub",
        "--sub-format",
        "vtt",
        "-o",
        output_template,
        url,
    ]
    if allow_auto:
        args.insert(4, "--write-auto-sub")

    result = runner(args)
    if result.returncode != 0:
        return None

    vtt_files = sorted(output_dir.glob("captions*.vtt"))
    if not vtt_files:
        return None

    all_segments = parse_vtt(vtt_files[0])
    scoped = filter_segments(all_segments, start_sec=start_sec, end_sec=end_sec)
    text = "\n".join(item.text for item in scoped)
    if len(text.strip()) < 20:
        return None

    source: Literal["youtube_caption", "youtube_auto_caption"] = (
        "youtube_caption" if ".auto." not in vtt_files[0].name else "youtube_auto_caption"
    )
    if allow_auto:
        source = "youtube_auto_caption"

    return TranscriptResult(source=source, text=text, segments=scoped)
