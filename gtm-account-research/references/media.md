# Conditional media work

Use this only for a substantive media lead. Do not require known timestamps before transcript review, assume every host is YouTube, or infer inaccessible recording from missing caption tracks. yt-dlp supports host-specific extractors; current YouTube/LinkedIn access must be tested, not promised universally.

## Captions first

`python3 scripts/media.py captions PUBLIC_URL --language en`

The helper obtains metadata without downloading media or saving extractor cache; it tries available manual then automatic caption tracks (json3/vtt/srt). Outputs JSON text with source-clock intervals. No usable track means local ASR may help, not that burned-in captions or the recording are absent. Do not claim this command watched frames. Retain JSON/text if needed as research evidence, not media.

## Consent and local fallback

Use [media-onboarding.md](media-onboarding.md) for the short setup/permission conversation, including tool updates, the base-model download and local compute. Reuse approved working setup. If captions are missing/inadequate and the user chose text/captions, use public alternatives or an explicit unreviewed-source limit; do not repeat setup requests. Reopen setup if the user requests it. Never use a paid API fallback.

After actual approval, record it privately:
`python3 scripts/media.py authorize --receipt PRIVATE/consent.json --authorization-reference 'actual user approval reference'`

A receipt records authorization; fabricating one is not approval. It is host-bound and reusable within scope. Do not bundle it.

Use an isolated Python environment and install scripts/requirements-media.txt only when authorized; yt-dlp and FFmpeg executables must be available. No import/setup is required for ordinary research. This helper does not silently install dependencies.

`PYTHON scripts/media.py transcribe PUBLIC_URL --receipt PRIVATE/consent.json --model-dir PRIVATE/models --language en`

For a user-approved existing compatible faster-whisper/CTranslate2 directory, replace `--model-dir PRIVATE/models` with `--model-path LOCAL_MODEL_DIRECTORY`. The helper requires local model.bin/config.json and loads with local_files_only=True, preventing a fallback download. A .pt file or whisper.cpp model is not interchangeable. Use the approved Python interpreter; no automatic conversion or installation. Output labels reused models as local-model, not assumed base.

The default cache route uses faster-whisper base on CPU/int8. If not cached, model download follows the receipt scope. No transcription API calls. Audio is selected and fetched by yt-dlp (`bestaudio/best`) into stdout, then decoded by FFmpeg from stdin into bounded PCM chunks (30 seconds with 1 second overlap), preserving absolute offsets. yt-dlp applies its native default/language ranking; do not override it by sorting raw formats by lowest bitrate. Default/original-track preference depends on the host metadata yt-dlp exposes; unknown track identity remains unknown. `--language` is an ASR hint, not a request to select a dubbed track. The `best` fallback supports hosts with combined audio/video formats. Overlap can repeat words; keep that boundary explicit rather than splice an invented quote. Chunking may affect recognition; base is not diarization. `--start`/`--duration` limit to a relevant interval; `--timeout` is a per-media safeguard (default 1200s), not a research-depth quota. The pipe is non-seekable: FFmpeg decodes/discards the prefix before `--start`, so late intervals can consume additional bandwidth/time. Timeout/errors return partial or failed coverage; do not call it full review. The stream-stage watchdog stops downloader/decoder processes; generator cleanup also handles early consumer exit. It does not forcibly interrupt an in-process speech-model call or include model-loading/metadata time. A producer cut off after FFmpeg reaches a requested duration is expected, while a premature failed download remains a failure. Model memory/compute remain platform-dependent.

No raw-media output files are created by this helper. Model/dependency storage, consent receipt and intentional evidence text are separate disk uses. Validate subprocess/temp/cache behavior in deployment before making stronger no-disk guarantees. Runtime limits/settings can be adjusted explicitly when needed; do not hide disk or paid fallback.

## Targeted verification

Read substantive transcript content, including unexpected workflow clues. Check decisive/ambiguous details: wording through selected audio/retranscription; speaker/artifact attribution through frames; independent sources for claims about actual practice. A second pass of the same model is not independent corroboration.

`python3 scripts/media.py frame PUBLIC_URL --at SECONDS` returns an in-memory JPEG as base64 JSON; forward it to the current tool's image viewer when supported. Do not save raw frames merely to bridge an unsupported UI. The helper does not yet provide an audio-playback frontend; use a supported in-memory audio tool when available, otherwise label audio listening unperformed. Local re-transcription is not listening.

Persist passages, source dates, transcript origin, selected intervals, actual review coverage and ambiguities in sources.json and retained text. No raw audio/video is needed in the delivered bundle. Failed public extraction permits appropriate public alternatives, not access-control bypasses.
