# Day2 Audio Pipeline Notes

## Scope

Day2 moves the project from a Day1 skeleton to a real native audio-processing path. The target is not full speech recognition yet, but a believable and testable C++ pipeline.

## Native implementation outline

### 1. WAV decoding

The C++ module now parses RIFF/WAVE bytes directly and validates:

- RIFF/WAVE header presence
- `fmt ` chunk existence
- PCM format
- 16-bit sample width
- `data` chunk presence

This keeps the core audio logic inside C++, which is exactly the architectural split described in the original planning document.

### 2. Frame slicing

Audio is split into fixed windows of 30 ms by default. Each frame gets:

- start time
- end time
- RMS energy estimate
- speech / non-speech flag

### 3. Energy VAD

Instead of pulling in an external VAD dependency on Day2, the pipeline uses:

- a base energy floor
- an adaptive threshold derived from the loudest frame
- grouping logic that tolerates short silence gaps

This is simple enough to explain in an interview and strong enough to show actual speech segmentation in the demo.

### 4. Speech segment grouping

Speech frames are merged into longer segments with:

- a minimum speech duration gate
- a maximum tolerated silence gap

This avoids returning a fragment for every tiny pause and makes the final transcript windows usable.

## Python-side mapping strategy

Because whisper.cpp text decoding is not attached yet, Python maps text onto the native windows in two ways:

- if `data/annotations/<filename>.txt` exists, the annotation text is split across the windows
- otherwise Day2 generates per-window mock text

That gives the API a realistic timestamped shape without pretending that full ASR is already done.

## Key files

- `cpp/audio_preprocess.cpp`
- `cpp/transcriber.cpp`
- `python/meeting_copilot/bridge.py`
- `python/meeting_copilot/services/transcription.py`

## Known limitation

The Day2 C++ module currently outputs speech windows, not decoded words. That is intentional. The next milestone should attach whisper.cpp so each native segment produces real transcript text.
