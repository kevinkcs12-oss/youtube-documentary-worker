# Pilot 01 — Executive decision gate QA and red-team v1.0

## Result

**PASS_CLOSED_GATES.** The decision surface is complete, but release mode correctly fails closed.

## Tests

- Current manifest schema and every enumerated option parse successfully.
- Normal review mode passes with publication held.
- Release mode returns a non-zero exit and identifies four unresolved decisions, `HOLD` publication, missing authorization ID and missing exact attestation.
- Timing authority remains v1.2f at 597.760 seconds; v1.2g remains only a reversible picture candidate.
- Voice labels remain blind; no candidate is ranked or selected.
- No-music and rights-cleared-music paths are distinct; neither grants spend or contact authority.
- Metadata choices preserve the three previously validated claim boundaries.

## Red-team findings

1. **Approval-by-silence:** rejected. Pending fields remain blocking.
2. **Partial authorization leakage:** rejected. Publication cannot open while any upstream choice is unresolved.
3. **Unlisted/public ambiguity:** rejected through separate scopes.
4. **Music-rights shortcut:** rejected. The rights-cleared path still requires asset-level provenance and review.
5. **Voice technical-pass inflation:** rejected. Technical audition status cannot become editorial or release approval.
6. **Validator overreach:** a successful decision manifest opens only downstream conform and preflight; it is not a publish command.

No purchase, paid credit, provider contact, upload or publication was performed.
