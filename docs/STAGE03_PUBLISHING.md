Stage 03: Publishing Factory
============================

Run tools/publish_factory.py with --snapshot --approval --company --output-root.
A six-field approval receipt must match evaluation_id, input_sha256 and
engine_sha256; decision must be approve and reviewer nonempty.
The builder replays the persisted input against the recorded scoring engine before
writing a site. It preserves decimal score precision so the displayed total and
grade use the same boundary. An existing company ID is rejected until the catalog
can store multiple evaluation versions without replacing the historical v1 row.
Builds a new standalone static site package including historical reports, a
versioned new report and SVG, generated industry and ranking Markdown, a
complete company JSON catalog, and a manifest. It NEVER overwrites master.
Human approval is an attestation, not proof of external fact-checking.
