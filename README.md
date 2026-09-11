# GTM Account Research

Research one supplied B2B prospect against your product context, then ask questions of the retained evidence. Company discovery and outreach are outside this skill.

## Install in a Codex project

Clone or download this repository, or extract the [release ZIP](releases/gtm-account-research-qa-r2.zip). Copy the `gtm-account-research` folder into your project's `.agents/skills/` directory, so the entry file is `.agents/skills/gtm-account-research/SKILL.md`. Start a new Codex session in that project. Preserve any existing customized installation before replacing it.

Invoke `$gtm-account-research`, then supply labeled seller and prospect URLs. For example:

Seller: Dalus https://dalus.io/ — Prospect: Voliro https://voliro.com/

Use your own company and prospect. You may also supply seller product documents; the skill distinguishes supported capabilities from assumptions.

## Setup

Use an agent with web/search tools and local Python 3. The research and Q&A helpers use Python's standard library. Firecrawl is recommended but optional; existing provider access may consume credits. Before new research, the skill asks which web tools it may use and whether to enable optional local transcription. It waits for your choices.

Text/captions-only research is supported. Video handling uses yt-dlp and FFmpeg when available. Optional local transcription uses faster-whisper and a base model (about 148 MB plus dependencies), with approval before setup/download/compute. A compatible existing faster-whisper/CTranslate2 model and Python environment can be supplied. No credentials, model weights or media tools are bundled. Configure credentials through the provider's normal local mechanism, not chat.

## Results and questions

The result is a structured evidence bundle: account.json, sources.json, research-log.json, retained source text and START_HERE.md. No PDF is required. Ask normal follow-up questions in the research session, such as: 'What do we know about how this company moves an experiment into a released product, and where might our product help?'

To reopen later, invoke the skill and point it at the completed bundle directory or ZIP, then ask your question. Existing-bundle Q&A works locally without new web research or media setup. Keep the bundle intact; retrieval caches belong outside it. Ask for a concise answer when desired.

## Tested configuration and limits

Astra at medium effort was used for the completed Voliro research runs and same-session Q&A. Focused fresh-session Q&A checks were also run during development. Comparable research depth across other models is not established. Use a strong reasoning model for research; discovery varies between runs.

The skill retains supporting passages, dates, contradictions and unknowns. Integrity checks verify record consistency, not the truth of publisher statements or exhaustive coverage. Public evidence cannot establish private purchasing intent, budget, or an unreported internal process. Product fit remains a hypothesis unless supported. Local transcription quality and source access depend on the environment and source.

## Release qa-r2 — September 10, 2026

Includes blocking onboarding, evidence-bundle Q&A and a focused final-coverage instruction: follow or specifically close consequential seller-relevant leads; justify redundancy against reviewed sections. No runtime code changed from qa-r1. Skill validation and 50 runtime/media/Q&A tests passed. The last coverage wording change has not had a separate behavioral replay. The same-session six-question check answered all core questions and 21/22 frozen checklist facets; that is a small functional test, not an accuracy benchmark.

## Development and verification

See [TESTING.md](TESTING.md) for reproducible local tests and the limits of the development evidence. The skill files match the qa-r2 release manifest.

## License

[MIT](LICENSE) © 2026 Luke Olson.
