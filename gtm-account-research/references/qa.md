# Explore a completed account

Use the same answering agent. No runtime reviewer or new research pass is required. Work from one explicitly selected exported bundle directory or ZIP; if the account/run is ambiguous, ask which one. Do not combine runs or treat private seller context as prospect evidence.

## Open and orient

Use the installed skill's scripts with absolute paths where needed. CACHE is a local writable working directory outside the immutable bundle; it holds only derived indices and ZIP extraction. Python's standard library is sufficient. No Firecrawl, embedding service or speech model is needed.

```sh
python3 scripts/qa.py --bundle BUNDLE --cache CACHE overview
python3 scripts/qa.py --bundle BUNDLE --cache CACHE catalog
```

The helper verifies the bundle on each invocation. Invalid/changed evidence fails closed; do not overwrite its manifest to make it pass. It safely extracts a ZIP into the cache and verifies the result. A valid new bundle fingerprint selects a new index. A damaged/unavailable index uses plain search; source access remains independent of the index. File hashing establishes integrity relative to the supplied manifest, not publisher truth or authenticity.

Keep the run identity, as-of date, seller-profile reference, scoped workflow picture and important limits in context. The catalog lists source titles/types/dates in bounded pages. Use `next_offset` by repeating the same command with global `--offset N` before its subcommand. Dates unknown in the inventory remain unknown. Do not load every full source or every reference file as orientation.

## Answer loop

1. Identify whether the user wants a fact, workflow, relevance judgment, challenge to a claim, or missing information. For a broad question, identify the relevant stages/aspects before searching; do not assume the first retrieved workflow is the whole answer.
2. Navigate source titles and search both original retained text and curated records. Reformulate a poor query or inspect a promising source directly. Inspect original sections around consequential hits, not snippets alone.
3. Follow existing claim/evidence links, conflicting evidence, and relevant questions/unknowns. Check subject, source date, event date, product version and excerpt coverage. A new scrape date is not a new publication; undated live pages do not establish a chronology of product maturity.
4. Answer directly with useful source links and stable IDs/locators. Distinguish reported facts, your inference and unknowns. For synthesized workflows, explain which stages come from distinct cases/versions rather than inventing a single observed process. Tailor relevance to the supplied seller without inventing integrations or commercial need.
5. If a material answer gap remains and the corpus has promising sections, keep reading. Otherwise explain the scoped limit. Search exhaustion means not found in the retained material, not real-world absence. New web research is separate and must respect the new-research setup choices.

Use prior conversation context for continuity, but verify additional claims against this run. A challenge should surface the strongest support and contrary evidence, not repeat the summary more confidently. Check unused pertinent aspects before finishing a broad answer; no numeric self-rating or fixed call quota determines Q&A completion.

## Retrieval commands

```sh
python3 scripts/qa.py --bundle BUNDLE --cache CACHE search 'version control purchasing'
python3 scripts/qa.py --bundle BUNDLE --cache CACHE source S12
python3 scripts/qa.py --bundle BUNDLE --cache CACHE read S12 --start 210 --end 235
python3 scripts/qa.py --bundle BUNDLE --cache CACHE read S12 --start 217 --section
python3 scripts/qa.py --bundle BUNDLE --cache CACHE record claim:C12
python3 scripts/qa.py --bundle BUNDLE --cache CACHE record evidence:E6
python3 scripts/qa.py --bundle BUNDLE --cache CACHE record question:Q5
python3 scripts/qa.py --bundle BUNDLE --cache CACHE record unknowns
python3 scripts/qa.py --bundle BUNDLE --cache CACHE record coverage
```

IDs above are illustrative, not facts about the current run. Other record keys: workflow:ID, action:ID, assessment. Search results expose actual IDs. Evidence records contain source locators and verification limits; source records include URL/date/coverage metadata.

Search uses SQLite FTS5/BM25 when available, otherwise case-insensitive plain lookup. `search 'terms' --plain` forces that fallback. Query terms are ORed; concise distinctive terms work better than a long sentence. No embedding dependency. Results show clipped snippets, source locators, dates and additional-result offsets. Exact duplicate chunk text is grouped; `--keep-duplicates` exposes all source instances when provenance/date comparisons matter. Do not count repeated copies as independent corroboration. Avoid rereading overlapping sections already in context unless checking a detail.

Default output is bounded to roughly6000 serialized characters; global `--max-chars` accepts2000–12000. This is a response-page size, not an account-research or answer-completeness budget. Paginate when truncated. `read` offsets index line fragments in the same requested range; preserve start/end/section on subsequent pages. Source/record offsets count characters in the same record. Long lines retain their line number and character offset. An oversized overview item can be read through the corresponding record command; inspect workflow records individually if needed.

If the hosting tool also truncates output, lower the page size and re-read. Never claim to have reviewed hidden text. A tool failure or unanswerable question should return an honest limitation, not an invented answer or automatic account rerun.
