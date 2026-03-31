# Day2 Test Report

## Automated tests

Executed with:

```powershell
C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe -m pytest
```

Observed result:

```text
3 passed, 1 warning in 0.58s
```

The warning comes from Starlette's current multipart import path and does not block Day2.

## Native build verification

Executed:

```powershell
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" -S . -B build -G "Visual Studio 17 2022" -A x64 -DPython3_EXECUTABLE="C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe"
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build --config Release
```

Observed result:

- configure succeeded
- Release build succeeded
- produced `build/cpp/Release/meeting_copilot_cpp.cp311-win_amd64.pyd`

## Health check

Observed `/health` response after build:

```json
{"status":"ok","service":"Meeting Copilot","version":"0.2.0-day2","cpp_backend_available":true,"cpp_backend":{"backend":"day2-native-audio-pipeline","version":"0.2.0","compiler":"MSVC"}}
```

## Functional Day2 check

A synthetic tone/silence/tone WAV sample was posted to `/transcribe`.

Observed result:

- `speech_segment_count = 2`
- `speech_duration_seconds = 0.9`
- transcript contained two timestamped text blocks
- backend reported `cpp-day2-vad+mock`
