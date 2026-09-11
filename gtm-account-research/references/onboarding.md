# Blocking setup before new research

This is a short conversation in the current terminal/chat, not a hosted page or installer. Existing-bundle Q&A skips this step. New seller/prospect web research waits until setup choices are resolved—even if authenticated tools are already present. Explicit choices already made for this run satisfy the gate; never ask twice for the same authorization.

## Detect locally

Read-only checks may identify OS, Python/environment, tool paths/versions, configured connector availability, and user-supplied model/cache locations. `PYTHON scripts/media.py status` only checks that Python's imports and executable discovery; absence there does not establish absence elsewhere. Do not inspect/print credential contents, run billable API probes, fetch package releases, load a model, install anything or begin seller/prospect retrieval while consent is pending. A locally visible Firecrawl configuration means available, not authorized. Avoid scanning the user's disk for models; check supplied paths and conventional caches only when useful.

## Ask once, then wait

Present a concise question tailored to detected capabilities, covering both:

- **Web extraction:** recommend Firecrawl as optional. Choose use the existing connection, help set it up, or continue with other available web tools. Explain that use may consume the user's Firecrawl credits. Do not request API keys in chat; use the provider's normal local authentication/configuration mechanism after approval. Firecrawl is not required.
- **Video fallback:** choose approved local transcription setup (base model about148MB plus dependencies), reuse a supplied compatible local environment/model, or text and captions only. Name proposed local paths, native install/update method and compute use. Disclose additional runtime/shared-tool changes separately. No paid transcription fallback.

Example: “Before research: may I use your existing Firecrawl connection, or should I use the other web tools? For videos without captions, should I set up local transcription (base model ~148MB plus dependencies), reuse a compatible setup you specify, or use text and captions only?” Tailor this rather than repeating options that do not exist.

Ask for a consequential missing choice if the reply resolves only one part. A request for setup details is not consent. With asynchronous input, do not continue research while waiting; end the turn or wait for the answer. No response is not approval. A decline resolves that capability choice; it does not prevent research using the remaining approved capabilities. Answer setup questions normally without fetching account sources.

## Resolve, record, start

After the choices, follow [media-onboarding.md](media-onboarding.md) only for approved media setup/reuse. Version checks over the network, downloads and smoke tests happen after approval of that scope. For reuse, inspect the selected interpreter and model format; use `--model-path` only for a local faster-whisper/CTranslate2 directory containing model.bin and config.json. That path loads locally only. A PyTorch .pt or whisper.cpp .bin is not automatically compatible; explain alternatives without converting/installing silently. Do not assume any local model has base's size or runtime.

Record the actual choices and authorization reference in private run setup notes: Firecrawl use/setup/decline, media setup/reuse/decline, approved paths and update/compute scope, detected capabilities and limitations. Do not fabricate consent from a receipt or environment variable. Keep these notes outside exported evidence. Summarize the usable tools, then begin seller/prospect research. Tool availability changes later do not silently broaden permission.
