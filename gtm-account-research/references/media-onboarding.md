# Approved media setup and reuse

Perform setup actions here only after the blocking choices in [onboarding.md](onboarding.md) are resolved. Reading these instructions to prepare a proposal is fine; pre-choice checks remain local and read-only. Reuse that actual approval; do not ask the same question again. This reference supplies environment-native setup details. Media support is optional; choosing text/captions permits research, but an unanswered setup question does not.

## Respect the approved setup scope

Inspect the host OS, available Python, yt-dlp and FFmpeg paths/versions, how those tools are installed/managed, local speech dependencies, a cached base model and actual prior authorization. Do not infer installation ownership from OS alone; inspect the resolved binary/package before selecting a manager. `python3 scripts/media.py status` checks presence, not versions, cached-model readiness or current host access. After approval for the relevant setup/version checks, check the latest stable yt-dlp release through its official release/package source; do not embed a permanently “latest” version. Reuse compatible tools/model and permission within its actual scope. A transcription receipt alone does not grant permission to update system tools.

Present one concise, tailored question. Example for a fresh environment:

> Optional: I can also research videos when captions are missing. May I set up the missing media tools using this environment’s existing installation method, download the base speech model (about 148 MB, plus dependencies), and use this machine to transcribe? This uses local compute rather than a paid transcription API. You can skip it and continue with captions and text.

Tailor that question to the actual tools and method, e.g. “update your Homebrew yt-dlp” or “install yt-dlp with your existing pipx setup,” plus any missing FFmpeg/transcription dependencies. Name the proposed local location and any additional required runtime or shared/system-level change before approval. For an existing setup, ask only about the missing download/update/compute permission. If approval already covers these actions, acknowledge it and proceed; do not ask again. Answer the user's questions normally. A yes applies to the described setup and use, not perpetual upgrades or unrelated installs. Record any broader update permission only if actually granted.

- **Yes:** set up the approved capabilities, check them, then briefly report what works and resume research.
- **No or not now:** retain that preference and continue with usable captions/text. Do not load/download the speech model or repeat the question for each video. Note inaccessible media when relevant.
- **Partial approval:** enable only the approved parts. A missing optional component does not block text research.

## After approval

Use the environment’s native, supported installation route for yt-dlp, rather than forcing pip or a new environment:

- Existing Homebrew, pipx, uv tool, pip/venv or OS-managed installation: use that manager’s supported targeted update/install command. Do not run a whole-environment upgrade or `yt-dlp -U` against a package-manager-owned binary.
- Official standalone executable: use its supported updater/replacement route. Do not assume every binary build supports self-update.
- Missing yt-dlp: prefer a suitable manager already used in this environment or the official platform binary. If ownership/method is unclear, explain the choice briefly rather than creating a competing installation blindly.

Consult current official installation guidance for exact commands; package-manager releases may lag upstream. Record available and installed versions without replacing an OS-managed package behind its manager’s back. A different installation route requires disclosure and applicable approval. Preserve the previous version and feasible native rollback/reinstall information; do not promise an automatic rollback the manager cannot provide.

Reuse working FFmpeg. Keep speech dependencies/model cache outside the skill package and exported account bundle; a private Python environment remains appropriate for ASR without requiring yt-dlp to live there. Verify the helper’s actual executable resolution after setup; a process-scoped PATH may select the approved native tool without editing global shell settings. Shared/system updates are allowed when the user has approved that actual scope. Check current yt-dlp runtime requirements (including JavaScript support for YouTube) through its official docs; any missing runtime belongs in the disclosed setup scope.

Install the optional scripts/requirements-media.txt into the approved Python environment. Follow [media.md](media.md) to record/reuse the real host-bound transcription authorization. Validate that authorization before loading/downloading the model. Preload faster-whisper's **base** model on CPU/int8 into the approved model cache; reuse cached weights instead of downloading twice. Setup stores dependencies/model files; raw audio/video still stays in pipes/RAM. No paid API fallback.

Run a short check: exact executable versions, dependency imports, model load, then captions and a brief streamed transcription on relevant accessible public media when available. Keep intervals small and within the user's resource allowance. Distinguish setup/model-load success, host access, transcript output and speech accuracy. If no suitable clip is available, mark media retrieval untested. A failed stream does not mean installation failed or every video on that host is blocked.

Keep private setup notes with actual approval scope/reference, tool paths and versions, model/cache location, checks, failures and permitted update scope. Never export the consent receipt, local paths, model or dependency environment with company evidence. Report capability-specific readiness briefly to the user.

## Later extraction failures

If a relevant video fails, check whether yt-dlp is outdated. When updating is already authorized, try one stable update through the detected installation method and retry the same URL/interval once; otherwise ask a short update question. Preserve before/after versions and outcomes, and retain feasible rollback/reinstall information for the prior version. Do not switch to nightly builds automatically, bypass access controls, or assume a 403 was caused by version age. If it still fails, use captions/public alternatives or retain an explicit access limit.

This is agent-guided setup, not an automatic installer. Detailed extraction/verification behavior remains in [media.md](media.md).

Official installation/update reference: https://github.com/yt-dlp/yt-dlp#installation . Use current guidance for the detected route, not a universal installer command.
