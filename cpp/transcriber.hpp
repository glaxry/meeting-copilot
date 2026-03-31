#pragma once

#include <string>
#include <vector>

namespace meeting_copilot {

struct RuntimeInfo {
    std::string backend;
    std::string version;
    std::string compiler;
};

struct SpeechSegment {
    double start_seconds;
    double end_seconds;
    int frame_count;
    int sample_count;
    double average_energy;
};

struct AudioAnalysisResult {
    int sample_rate_hz;
    int channels;
    int total_frame_count;
    double duration_seconds;
    double speech_duration_seconds;
    std::vector<SpeechSegment> speech_segments;
};

RuntimeInfo GetRuntimeInfo();
std::string DescribeAudio(int sample_rate_hz, int frame_count);
AudioAnalysisResult AnalyzeAudioBytes(
    const std::string& audio_bytes,
    int frame_ms = 30,
    double base_energy_threshold = 0.015,
    int min_speech_ms = 240,
    int max_silence_ms = 180
);

}  // namespace meeting_copilot
