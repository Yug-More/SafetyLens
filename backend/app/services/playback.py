"""Create browser-compatible H.264 derivatives; never overwrite original evidence."""

from pathlib import Path
import subprocess
from app.core.config import get_settings
from app.core.errors import AppError
from app.services.storage import resolve_upload_path


def playback_path(stored_filename, settings=None):
    return resolve_upload_path(stored_filename + ".playback.mp4", settings)


def prepare_playback(stored_filename, settings=None):
    import imageio_ffmpeg

    cfg = settings or get_settings()
    source = resolve_upload_path(stored_filename, cfg)
    target = playback_path(stored_filename, cfg)
    temporary = target.with_suffix(".partial.mp4")
    try:
        subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-nostdin",
                "-v",
                "error",
                "-y",
                "-protocol_whitelist",
                "file",
                "-threads",
                "1",
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-an",
                "-t",
                str(cfg.max_video_duration_seconds),
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "24",
                "-pix_fmt",
                "yuv420p",
                "-threads",
                "1",
                "-movflags",
                "+faststart",
                str(temporary),
            ],
            check=True,
            timeout=90,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        temporary.replace(target)
    except (OSError, subprocess.SubprocessError) as exc:
        temporary.unlink(missing_ok=True)
        raise AppError(
            "PLAYBACK_ENCODING_FAILED",
            "Browser playback derivative could not be prepared; original evidence retained.",
            422,
        ) from exc
    return target
