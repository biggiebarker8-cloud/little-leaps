# little-leaps
Children's learning games 

## Content-pack contract

All content packs live under `packs/<type>/` as static JSON data and must
validate against [`schemas/content-pack.schema.json`](schemas/content-pack.schema.json),
using a JSON Schema validator that supports Draft 2020-12.

Every pack requires `id`, `title`, `ageBand`, `type`, `version`, `reviewStatus`,
and `screens`. IDs should remain stable and unique across packs. `version` is a
positive integer content revision. `screens` is an array of screen objects;
individual activity types define their screen fields. Empty screen arrays are
allowed for unfinished packs, but do not make a pack ready for release.

The shared schema intentionally allows additional fields and new age bands or
activity types, so stories, matching games, and other activities can share the
same metadata contract. Activity-specific validation supplements this contract;
it must not replace or relax the required fields or review-status restrictions.

## Safety review and release

`reviewStatus` must be one of:

- `draft`: content is being authored.
- `pending-review`: content is awaiting actual child-safety/compliance review.
- `approved`: this exact content revision has passed actual child-safety and
  applicable compliance review.
- `rejected`: review found issues that must be addressed before approval.

**Internal approval, automated checks, and schema validation are not
child-safety/compliance review and must never justify `approved`.** Record the
reviewer, reviewed pack ID/version, date, scope, and outcome in the release review
record, outside child-facing pack data. If that review has not happened, do not
mark the pack approved. Content changes require a version increment and a return
to `draft` or `pending-review` for a fresh review.

Only reviewed, approved revisions may be released to children. A future release
pipeline and engine must validate packs and enforce that gate; a pack's
self-declared status alone is not proof of approval. The current
`safe-secrets-01` pack is an unfinished, pending-review pack, not release-ready.

## Engine and content separation

This repository currently contains content data, not an app engine or download
service. Keep any future engine separate from `packs/`: packs are data, never
executable code. The engine should load and validate packs through the shared
contract and dispatch supported activity types to reusable renderers. Reject
invalid packs and unsupported types safely rather than executing pack content.

New age groups, stories, matching games, and other activities that use existing
engine capabilities should be delivered as independently versioned packs without
rebuilding the core app. Genuinely new interaction mechanics may require an
engine update; adding a new `type` value alone does not implement a renderer.
Future downloadable packs should remain separately distributed static data,
with their reviewed revision verified before use.

For now, keep all child-facing content local/static. Do not add a backend,
remote content fetching, or a download service unless a future feature genuinely
requires one. Do not add analytics, ads, tracking, chat, accounts, location
collection, or unnecessary personal-data collection.

## Validation

With Python 3.12 installed, run from the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate_packs.py
python -m unittest discover -s tests
```

The validator checks that the shared schema is valid Draft 2020-12 JSON Schema
and validates every JSON file recursively under `packs/`. It exits nonzero for
invalid packs, malformed JSON, an invalid schema, or no packs. GitHub Actions
runs validation and regression tests on every pull request and push to `main`;
invalid packs fail CI. The only direct development dependency is `jsonschema`;
there is no app build or runtime service.

Also apply activity-specific checks and the actual safety-review process
described above; schema validation alone is not release approval and does not
change a pack's version or review status.
