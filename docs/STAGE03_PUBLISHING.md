Stage 03: Publishing Factory
============================

Run tools/publish_factory.py with --snapshot --approval --company --output-root.
A six-field approval receipt must match evaluation_id, input_sha256 and
engine_sha256; decision must be approve and reviewer nonempty.
Builds a new standalone static site package including historical reports, a
versioned new report and SVG, generated industry and ranking Markdown, a
complete company JSON catalog, and a manifest. It NEVER overwrites master.
Human approval is an attestation, not proof of external fact-checking.
