Day3 stores runtime transcription logs here.

Each `/transcribe` call writes one JSON file containing:

- audio metadata
- transcript segments
- incremental transcription events
- notes about the backend path used

The generated `.json` files are intentionally ignored by Git.
