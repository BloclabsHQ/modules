"""Exercise SNS package inputs through the pinned Lambda module's real builder."""

import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile


SNS = Path(__file__).resolve().parents[1]
BUILDER_SHA256 = "9ad2f39ce95cddb5c6460d8eeab543c5e3ab1c858910556f4e3a5f76910948b8"


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        supplied = os.environ.get("SNS_LAMBDA_PACKAGE_SCRIPT")
        if not supplied:
            raise RuntimeError("Set SNS_LAMBDA_PACKAGE_SCRIPT to Lambda 6.4.0 package.py")
        cls.builder = Path(supplied).resolve(strict=True)
        if hashlib.sha256(cls.builder.read_bytes()).hexdigest() != BUILDER_SHA256:
            raise RuntimeError("SNS package builder does not match reviewed Lambda 6.4.0")
        source = (SNS / "slack/main.tf").read_text()
        selected = re.findall(r'source_path\s*=\s*\[\{\s*path\s*=\s*"([^"\n]+)"\s*\}\]', source)
        if len(selected) != 1 or not selected[0].startswith("${path.module}/"):
            raise RuntimeError("Expected one SNS source-path object rooted at path.module")
        cls.source_path = selected[0].replace("${path.module}", "slack", 1)
        cls.handler = (SNS / "slack/functions/app.py").read_bytes()

    def build(self, manifest, handler=None):
        with tempfile.TemporaryDirectory(prefix="sns-package-") as temporary:
            cwd = Path(temporary)
            functions = cwd / "slack/functions"
            functions.mkdir(parents=True)
            app = functions / "app.py"
            app.write_bytes(self.handler if handler is None else handler)
            app.chmod(0o644)
            os.utime(app, (1577836800, 1577836800))
            (functions / ".terragrunt-source-manifest").write_text(manifest)
            query = {
                "paths": json.dumps({"module": "lambda", "root": ".", "cwd": str(cwd)}),
                "docker": None,
                "artifacts_dir": "builds",
                "runtime": "python3.10",
                "source_path": json.dumps([{"path": self.source_path}]),
                "hash_extra": "",
                "hash_extra_paths": "[]",
                "recreate_missing_package": "false",
            }
            environment = {"PATH": os.environ["PATH"], "LC_ALL": "C", "TZ": "UTC",
                           "TF_LAMBDA_PACKAGE_LOG_LEVEL": "ERROR"}
            prepared = subprocess.run(
                [sys.executable, str(self.builder), "prepare"], input=json.dumps(query),
                cwd=cwd, env=environment, text=True, capture_output=True, check=True,
            )
            result = json.loads(prepared.stdout)
            subprocess.run(
                [sys.executable, str(self.builder), "build", "--timestamp", result["timestamp"],
                 result["build_plan_filename"]],
                cwd=cwd, env=environment, text=True, capture_output=True, check=True,
            )
            archive = (cwd / result["filename"]).read_bytes()
            with zipfile.ZipFile(io.BytesIO(archive)) as package:
                entries = package.namelist()
                contents = package.read("app.py")
            return result["filename"], archive, entries, contents

    def test_generated_manifest_does_not_change_package(self):
        first = self.build('{"source":"/checkout/one"}')
        second = self.build('{"source":"/different/checkout/two"}')
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[2], ["app.py"])
        self.assertEqual(second[2], ["app.py"])
        self.assertEqual(first[3], self.handler)

    def test_handler_change_changes_package(self):
        first = self.build("same metadata")
        changed = self.handler + b"\n# Changed source fixture\n"
        second = self.build("same metadata", changed)
        self.assertNotEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])
        self.assertEqual(second[2], ["app.py"])
        self.assertEqual(second[3], changed)


if __name__ == "__main__":
    unittest.main()
