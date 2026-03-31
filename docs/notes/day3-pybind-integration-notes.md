# Day3 Pybind Integration Notes

## Source document summary

Day3 is defined as the pybind11 packaging and Python integration milestone:

- open the cross-language call path
- make Python receive incremental transcription results
- store transcription logs
- connect the result to FastAPI `/transcribe`

## Design choices

### Promote C++ from analysis-only to transcript-event producer

Day2 stopped at speech-window detection. Day3 moves the C++ boundary one step forward so the native layer returns both:

- transcript segments
- incremental transcript events

This better matches the project document's requirement that Python should receive transcription results rather than just low-level audio features.

### Keep text deterministic for this milestone

The project plan separates Day3 pybind integration from Day4 summary generation and later model-based features. Instead of introducing an unstable ASR dependency early, Day3 keeps transcript text deterministic:

- use annotation sidecars when available
- otherwise generate mock text

That keeps the bridge testable while preserving a realistic JSON shape for future `whisper.cpp` integration.

### Write one JSON log per transcription call

Each `/transcribe` request now produces a JSON log under `reports/transcriptions/`. The log captures:

- source filename
- audio metadata
- transcript segments
- incremental events
- backend notes

This is useful for experiments, demos, and later report writing.

## Implementation notes

### Native layer

- `cpp/transcriber.cpp` now defines transcript chunk and event structures
- `TranscribeAudioBytes(...)` reuses Day2 VAD output and builds `partial` + `final` events
- `cpp/bindings.cpp` exposes the new function as `transcribe_audio_bytes(...)`

### Python layer

- `python/meeting_copilot/bridge.py` loads the new native symbol when present
- `python/meeting_copilot/services/transcription.py` parses native events, falls back safely, and writes logs
- `python/meeting_copilot/schemas.py` now includes `TranscriptEvent` and `TranscriptionLogMetadata`

### Test fixture

`data/annotations/annotated_sync.txt` was added so Day3 can verify the annotation-backed native path without depending on any external dataset.

## Risks and follow-up

- transcript text is still not model-generated, so semantic quality is not yet meaningful
- incremental events are simulated from chunked text rather than streamed from a real decoder
- Day4 should reuse the Day3 logs and transcript structure instead of inventing a separate intermediate format
