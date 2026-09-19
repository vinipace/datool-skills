#!/usr/bin/env python3
"""Exercise artifact rejection without Docker, network, secrets or production."""

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/datool-deploy/scripts/verify_artifact.py"
SPEC = importlib.util.spec_from_file_location("verify_artifact", SCRIPT)
VERIFIER = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(VERIFIER)
SHA = "a" * 40


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name)
        (self.bundle / "image.tar.gz").write_bytes(b"fixture archive; validator does not interpret Docker contents")
        (self.bundle / "image-ref.txt").write_text(f"datool-release:{SHA}-123-1\n")
        (self.bundle / "image-size.txt").write_text("2048\n")
        self.manifest()

    def manifest(self):
        entries = []
        for name in sorted(VERIFIER.FILES):
            digest = hashlib.sha256((self.bundle / name).read_bytes()).hexdigest()
            entries.append(f"{digest}  {name}\n")
        (self.bundle / "image.sha256").write_text("".join(entries))

    def check(self, commit=SHA, run=None):
        return VERIFIER.verify(self.bundle, commit, run)

    def test_valid_ci_and_manual_bundle(self):
        self.assertEqual(self.check(run="123")["image_bytes"], 2048)
        self.assertEqual(self.check()["commit"], SHA)

    def test_modified_archive_rejected(self):
        (self.bundle / "image.tar.gz").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            self.check()

    def test_wrong_commit_or_run_rejected(self):
        for commit, run in [("b" * 40, None), (SHA, "456"), ("main", None), (SHA, "0")]:
            with self.subTest(commit=commit, run=run), self.assertRaises(ValueError):
                self.check(commit, run)

    def test_unsafe_or_missing_manifest_entries_rejected(self):
        original = (self.bundle / "image.sha256").read_text()
        for text in [original.replace("image.tar.gz", "../image.tar.gz"),
                     original + original.splitlines()[0] + "\n",
                     "\n".join(original.splitlines()[:-1]),
                     original.replace("image.tar.gz", "/tmp/image.tar.gz")]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                (self.bundle / "image.sha256").write_text(text)
                self.check()

    def test_symlink_rejected(self):
        original = self.bundle / "image.tar.gz"
        original.rename(self.bundle / "target")
        original.symlink_to("target")
        with self.assertRaisesRegex(ValueError, "non-symlink"):
            self.check()

    def test_invalid_tags_rejected_even_with_correct_checksum(self):
        for tag in [f"datool-release:{SHA}-0-1", f"datool-release:{SHA}-123-0",
                    f"datool-release:{SHA}-123-1;id", "dokku/datool:latest"]:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                (self.bundle / "image-ref.txt").write_text(tag)
                self.manifest()
                self.check()

    def test_size_limits(self):
        for size in ["0", "-1", "1.2", "2;id", str(VERIFIER.MAX_IMAGE_BYTES + 1)]:
            with self.subTest(size=size), self.assertRaises(ValueError):
                (self.bundle / "image-size.txt").write_text(size)
                self.manifest()
                self.check()
        (self.bundle / "image-size.txt").write_text(str(VERIFIER.MAX_IMAGE_BYTES))
        self.manifest()
        self.assertEqual(self.check()["image_bytes"], VERIFIER.MAX_IMAGE_BYTES)

    def test_cli_failure_and_success(self):
        for commit, code in [(SHA, 0), ("b" * 40, 1)]:
            result = subprocess.run([sys.executable, str(SCRIPT), str(self.bundle),
                                     "--commit", commit], capture_output=True, text=True)
            self.assertEqual(result.returncode, code)
            if code:
                self.assertIn("Artifact rejected:", result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
