# Pilot 01 — Chained Release Preflight QA v1.0

## Verdict

`PASS_CHAINED_PREFLIGHT_ONLY` for the synthetic positive fixture. The live project remains `HOLD`; no final voice, authorization-bound audio conform, final master, upload, or publication was produced.

## Material change

The downstream preflight now binds the previously independent controls into one fail-closed chain:

1. the 32-check technical baseline must remain `PASS_WITH_HUMAN_GATES` with zero failures and its three explicit human gates;
2. the canonical executive v1.1 validator must return `DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT`;
3. the audio result must be schema v1.3, non-fixture, authorization-bound, and byte-matched to the supplied media;
4. the executive manifest SHA-256, motion decision, picture variant, pinned picture SHA-256, and publication scope must all agree;
5. the narration verdict must be `PASS_NARRATION_CONFORM_ONLY`, with 91-take lineage hashes present and fixture mode false;
6. the locked technical contract remains 597.760 s, 14,944 frames, 1920×1080, 25 fps, mono 48 kHz.

Every successful output is still forced to `final_master_present=false`, `upload_authorized=false`, `publishable=false`, `release_authorized=false`, and `preflight_only=true`. This tool can certify readiness for downstream master assembly; it cannot grant release authority.

## Adversarial QA

- 13/13 new tests passed.
- 8/8 picture-decision binding regressions passed.
- 9/9 executive-handoff regressions passed.
- 9/9 narration-provenance regressions passed.
- Python compilation passed.

The new suite rejects: a `HOLD` manifest; incomplete executive decisions; the wrong audio schema; dry-run audio; fixture narration; decision-manifest or media hash divergence; motion, picture, or publication-scope disagreement; a failed technical baseline; an upstream publication-authority claim; malformed lineage hashes; and non-finite duration values.

## Red-team findings

During review, a non-finite JSON number could have bypassed the duration comparison because comparisons involving `NaN` are false. The validator now requires a finite duration and the test matrix includes this attack. Lineage values are also constrained to lowercase 64-character SHA-256 strings, and duplicate/missing baseline human gates are rejected.

Residual boundary: this preflight trusts the validated v1.3 result only after matching its output hash to the supplied media. It does not create or label a final master and does not upload anything. The real positive path cannot be exercised until Kevin supplies all eleven human decisions, an explicit authorization identifier and attestation, and a non-fixture 91-take narration delivery.

## Reproducibility

- Validator SHA-256: `a22f76c201cc12c525f2a64af85c241c79d6f2dab1e0ca97538daeb843379148`
- Test runner SHA-256: `e5acfa2ef7c436f7e9241c921107cc8d1b2ab7afab7b5744a675bb56b4e57e67`
- Test matrix SHA-256: `7164fed85e5f1979c226f55114056f0d80988a4c9eef07e5d907d921c5fded4e`

No paid model, external asset, third-party contact, upload, or publication was used.
