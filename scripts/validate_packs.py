import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


ROOT = Path(__file__).resolve().parents[1]


def validate_packs(packs_dir, schema_path):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    packs = sorted(packs_dir.rglob("*.json"))
    if not packs:
        raise ValueError(f"No content packs found in {packs_dir}")

    valid = True
    for path in packs:
        try:
            pack = json.loads(path.read_text(encoding="utf-8"))
            validator.validate(pack)
        except (OSError, UnicodeError, ValueError, ValidationError) as error:
            print(f"INVALID {path}: {error}", file=sys.stderr)
            valid = False

    if valid:
        print(f"Validated {len(packs)} content pack(s).")
    return valid


def main():
    try:
        return 0 if validate_packs(
            ROOT / "packs", ROOT / "schemas" / "content-pack.schema.json"
        ) else 1
    except (OSError, UnicodeError, ValueError, SchemaError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
