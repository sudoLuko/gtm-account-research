# Research records (V2 / schema 2.0)

Exact fields/types live in schemas/account.schema.json, sources.schema.json and research-log.schema.json. Read the relevant schema when constructing each record; the entrypoint does not load all field definitions. These files are run data. Seller-profile schema version 1.0 is separate and private.

## Account and source links

account.json contains profile ID/revision/SHA-256, prospect identity, claims, workflows and assessment. Claims: reported (attributed assertion, not verified truth), inferred or unresolved; supporting and conflicting evidence IDs plus scope limits. Workflows reference individual step and connection claims. Label inferred connections. Never assemble unrelated cases into an asserted procedure.

sources.json contains sources and evidence. Retain reviewed text once in sources/NAME.md (txt/vtt/json also allowed). Quote exact retained text with 1-based inclusive line_start/line_end and a descriptive page/section locator. Media evidence also carries source-clock start/end seconds. The validator checks literal support after whitespace normalization; it does not certify interpretation, speaker truth or time alignment. For paraphrase, quote its actual supporting passage and explain the interpretation separately.

Sources distinguish publication/upload, event, retrieval and review dates. Partial publication dates use YYYY or YYYY-MM; unknown is null plus notes. Exact timestamps include a timezone. Record extracted_coverage separately from reviewed_coverage. A full automatic transcript can be only selectively reviewed. Missing body cannot support a workflow assertion; searched/unopened jobs remain identifiable. derived_from/correction_note preserve transformations and corrections. Each source records actions that exposed or retrieved it.

## One queue, action history and checkpoints

research-log.json contains actions, questions, rounds, checkpoints and final_assessment. Source discoveries, proposed routes and actual retrievals are different. For actions retain actual query/URL/tool arguments as text, time when observed (null if unknown), status, outcome, source IDs and question IDs. correction_of links a later correction without rewriting original action outcomes. Never manufacture timings after the fact.

Questions retain identity, original wording, parent relationships, source cue, value, status/reason, next action and reopen condition. Use next action for open/active questions; resolved routes retain their reason. Rounds link actual actions and independently describe finding_gain, route_gain, verification_gain and the next decision.

Record baseline (round_id=null) and each meaningful round's six dimension ratings. Each dimension has score 1–10, basis, evidence IDs, question IDs, change and next action. Empty evidence at baseline is honest. No mean score or score-triggered stop. Final assessment contains coverage review, unexplored areas, linked gaps, stop reason and reopening condition. Distinguish complete, budget_limited, access_limited, needs_input and in_progress. If a material access-blocked lead remains, use access_limited rather than claiming completeness; irrelevant/answered public alternatives can close a branch for an explicit reason.

## Timing and unused-lead review

Persist the baseline before the first prospect-source request. At a round boundary, record that round's real actions and findings, update the question queue, then append its checkpoint and save research-log.json before making the next round's request. Do this before synthesis for the final round too. Use a clock-derived recording timestamp, not the time the source was published or an invented historical time. Checkpoint at means when recorded; action at means the observed request time and may be null if unknown. Do not rewrite earlier scores after learning later facts. A missed checkpoint must be identified in its basis/change and in START_HERE.md as retrospective; record its actual creation time and do not claim faithful checkpoint execution. Existing structural validation cannot prove this behavior; the upcoming fresh runs must test it against request records.

When discovery exposes a promising public artifact, keep its URL/title in a question's cue/next_action and link the exposing source through source_ids. Add or update a question when the lead could materially improve understanding; do not create one for every search result. During the final review, revisit these cues and unused links from inspected material, adding any overlooked consequential route to the same queue. For each such route, pursue it or retain the applicable status, specific reason and remaining action/reopen condition. A title/snippet supports triage, not a claim that the body was reviewed.

Judge a source's possible contribution separately from a claim it cannot establish: a scoped source can describe artifacts, controls or handoffs without proving current universal practice or buying need. Repetition requires an explanation of what is already covered. A contact-only question does not absorb public workflow/version gaps. Write the reviewed question IDs, useful additions, closure reasons and remaining public limits into final_assessment.coverage_review/unexplored. Use existing fields; no second ledger or new source quota is required.

## Validation and export

`python3 scripts/validate.py run RUN [--final]` checks schemas, IDs, passages, timestamps, round checkpoints and honest unfinished statuses. `--final` refuses in_progress. It does not grade research quality or guarantee public accessibility. Complete meaningful source/claim review before export.

Run data can include private seller-profile.json, consent receipts and build intermediates outside sources/. Exporter uses an explicit allowlist: account.json, sources.json, research-log.json, START_HERE.md and referenced prospect text. Internal seller docs/code do not belong in those fields or in sources/. It detects some obvious private paths/secrets but cannot certify arbitrary prose is safe to export.

Metadata corrections and raw returned source text may contain signed download URLs. Keep those private outside the export; create a declared normalized text derivative without credentials/expiring links, with locators that resolve to the exported derivative. Do not silently edit quoted prose to pass validation.
