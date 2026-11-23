"""news-image-20261123 entry: write the bundled image to the output folder.

The image itself is `entry.png` next to this file: a one-page summary of
world news for Monday 23 November 2026 (29 stories, six regions, lead
story the COP31 collapse in Antalya). This program only copies that file,
checks it is a valid 1024x1024 PNG under 1 MiB, and verifies the copy.

Standard library only. No network. Running it twice writes identical
bytes, because the source file never changes during a run.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def fail(message):
    print("error: " + message, file=sys.stderr)
    raise SystemExit(1)


def bundled_image():
    here = Path(__file__).resolve().parent
    candidate = here / "entry.png"
    if not candidate.is_file():
        fail("entry.png is missing next to main.py")
    return candidate


def check_png(data):
    if len(data) > MAX_BYTES:
        fail("entry.png is %d bytes, over the 1 MiB limit" % len(data))
    if data[:8] != PNG_MAGIC:
        fail("entry.png does not start with the PNG signature")
    if len(data) < 33 or data[12:16] != b"IHDR":
        fail("entry.png has no IHDR chunk where one is expected")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
        fail("entry.png is %dx%d, expected 1024x1024" % (width, height))
    if data[-12:] != b"\x00\x00\x00\x00IEND\xaeB`\x82":
        fail("entry.png does not end with a proper IEND chunk")


def pick_output_folder(argv):
    for position, value in enumerate(argv):
        if value == "--out" and position + 1 < len(argv):
            return Path(argv[position + 1])
    if len(argv) > 1 and not argv[1].startswith("-"):
        return Path(argv[1])
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.environ.get("OUTPUT_DIR")
    if env_dir:
        return Path(env_dir)
    return Path("/output")


def digest(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main(argv):
    source = bundled_image()
    with open(source, "rb") as handle:
        data = handle.read()
    check_png(data)
    target_dir = pick_output_folder(argv)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "entry.png"
    shutil.copyfile(source, target)
    if target.stat().st_size != len(data):
        fail("the copied file has an unexpected size")
    if digest(target) != digest(source):
        fail("the copied file does not match the bundled image")
    print("wrote %s (%d bytes)" % (target, len(data)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
