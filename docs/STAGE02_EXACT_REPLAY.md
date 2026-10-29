# Stage 02: Exact Replay for New Evaluation Snapshots

For new evaluations only:

    python3 tools/replay_evaluations.py --input data/evaluations/id/snapshot.json
    python3 tools/replay_evaluations.py --directory data/evaluations

Checks current v1 engine SHA256, canonical input SHA256, immutable evaluation
ID, and full score result equality. Any mismatched score or changed scoring
code fails. The directory mode emits verified/failed counts.

If the original engine bytes are no longer available, replay refuses to
pretend the current engine matches the recorded one. Archive immutable engine
versions when performing a future scoring engine migration.

This does NOT recover the missing 23 indicator levels for the original 230
company reports. Historical discrepancies remain flagged in the legacy
precision ledger until supported original inputs are restored.
