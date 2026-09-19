#!/usr/bin/env python3
"""Validate Datool's image bundle without loading it or contacting production."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


FILES = {"image.tar.gz", "image-ref.txt", "image-size.txt"}
MAX_IMAGE_BYTES = 8 * 1024**3


def regular_file(directory, name):
    path = directory / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected a regular, non-symlink file: {name}")
    return path


def small_text(path, limit=4096):
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Metadata too large: {path.name}")
    return data.decode("ascii")


def verify(directory, commit, run=None):
    directory = Path(directory)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full lowercase 40-character commit SHA")
    if run is not None and not re.fullmatch(r"[1-9][0-9]*", run):
        raise ValueError("Expected a positive run number")

    entries = {}
    checksum_file = regular_file(directory, "image.sha256")
    for line in small_text(checksum_file).splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *](.+)", line)
        if not match or match[2] not in FILES or match[2] in entries:
            raise ValueError("Invalid, duplicate or unexpected checksum entry")
        entries[match[2]] = match[1].lower()
    if set(entries) != FILES:
        raise ValueError("Checksum manifest must cover exactly the three image files")

    for name, expected in entries.items():
        digest = hashlib.sha256()
        with regular_file(directory, name).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}")

    image = small_text(directory / "image-ref.txt").strip()
    match = re.fullmatch(r"datool-release:([0-9a-f]{40})-([1-9][0-9]*)-([1-9][0-9]*)", image)
    if not match or match[1] != commit:
        raise ValueError("Image reference does not match the expected commit or tag format")
    if run is not None and match[2] != run:
        raise ValueError("Image reference does not match the expected CI run")
    size_text = small_text(directory / "image-size.txt").strip()
    if not re.fullmatch(r"[1-9][0-9]*", size_text):
        raise ValueError("Expected a positive image size in bytes")
    size = int(size_text)
    if size > MAX_IMAGE_BYTES:
        raise ValueError("Declared image size exceeds the restricted import limit of 8 GiB")
    return {"commit": commit, "image": image, "image_bytes": size,
            "release_number": match[2], "attempt": match[3],
            "archive_sha256": entries["image.tar.gz"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run", help="Require the independently verified GitHub run ID")
    args = parser.parse_args()
    try:
        result = verify(args.directory, args.commit, args.run)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Artifact rejected: {error}\n")
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
