from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jsonschema.exceptions import SchemaError

from scripts.validate_packs import ROOT, main, validate_packs


class ValidatePacksTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.packs = Path(self.temp.name) / "packs"
        self.packs.mkdir()
        self.schema = ROOT / "schemas" / "content-pack.schema.json"
        self.pack = json.loads(
            (ROOT / "packs" / "story-choice" / "safe-secrets-01.json").read_text(
                encoding="utf-8"
            )
        )
        self.output = StringIO()
        self.enterContext(redirect_stdout(self.output))
        self.errors = StringIO()
        self.enterContext(redirect_stderr(self.errors))

    def write_pack(self, pack, name="pack.json"):
        path = self.packs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(pack), encoding="utf-8")
        return path

    def test_valid_unfinished_pack_and_extensible_metadata(self):
        self.pack.update(ageBand="new-age-band", type="new-type", extra="static data")
        self.write_pack(self.pack, "nested/type/pack.json")
        self.assertTrue(validate_packs(self.packs, self.schema))

    def test_invalid_contract(self):
        for field in self.pack:
            with self.subTest(missing=field):
                pack = self.pack.copy()
                del pack[field]
                self.write_pack(pack)
                self.assertFalse(validate_packs(self.packs, self.schema))
        for field, value in (
            ("id", ""), ("title", ""), ("ageBand", ""), ("type", ""),
            ("version", 0), ("version", True), ("version", "1"),
            ("reviewStatus", "internally-approved"),
            ("screens", {}), ("screens", ["executable content"]),
        ):
            with self.subTest(field=field, value=value):
                self.write_pack({**self.pack, field: value})
                self.assertFalse(validate_packs(self.packs, self.schema))

    def test_checks_every_pack_including_malformed_json(self):
        self.write_pack(self.pack)
        bad = self.write_pack({}, "nested/bad.json")
        malformed = self.packs / "malformed.json"
        malformed.write_text("{", encoding="utf-8")
        self.assertFalse(validate_packs(self.packs, self.schema))
        self.assertIn(str(bad), self.errors.getvalue())
        self.assertIn(str(malformed), self.errors.getvalue())

    def test_invalid_schema_fails(self):
        self.write_pack(self.pack)
        schema = Path(self.temp.name) / "schema.json"
        schema.write_text('{"type": "not-a-type"}', encoding="utf-8")
        with self.assertRaises(SchemaError):
            validate_packs(self.packs, schema)

    def test_no_packs_fails(self):
        with self.assertRaises(ValueError):
            validate_packs(self.packs, self.schema)

    def test_invalid_pack_returns_failure_exit_code(self):
        root = Path(self.temp.name)
        (root / "schemas").mkdir()
        (root / "schemas" / "content-pack.schema.json").write_text(
            self.schema.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.write_pack({})
        with patch("scripts.validate_packs.ROOT", root):
            self.assertEqual(main(), 1)

    def test_command_works_from_another_directory(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_packs.py")],
            cwd=self.temp.name, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
