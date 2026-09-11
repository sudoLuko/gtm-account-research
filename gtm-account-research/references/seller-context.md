# Seller context

Use the existing conversation or explicitly supplied/referenced files/pages. If insufficient, ask: “What product are we qualifying accounts for, and where should I read about it?” Do not scan unrelated repositories. Save seller-profile.json as private run data, outside the exported prospect source directory.

Follow schemas/seller-profile.schema.json. Claims distinguish seller_confirmed, source_reported and inferred, with source references, availability, scope and limits. Supported commercial availability needs explicit scope-appropriate evidence; code or demos alone do not establish it. Dates retain original precision. Missing values remain null/gaps. Conflicting capabilities remain visible; clarify a blocking conflict instead of choosing the strongest claim.

Ready means identity/scope and a non-inferred capability provide a meaningful research basis. ready_with_limits permits nonblocking uncertainty. needs_input means a useful assessment cannot proceed; do not manufacture fit hypotheses. Hypotheses can initially be empty and never imply buying intent.

Reuse profiles across accounts. Increment revision on relevant content changes; earlier accounts retain their exact revision and SHA-256. Do not recrawl the seller automatically. A prospect's constraints can expose a seller gap, not establish a new feature. Export only profile ID/revision/hash, not underlying private documents or internal paths.

Validate with `python3 scripts/validate.py seller PATH/seller-profile.json`. Schema reference paths are relative to the skill directory, not a presumed user workspace.
