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

struct TranscriptChunk {
    int chunk_index;
    double start_seconds;
    double end_seconds;
    std::string text;
    double confidence;
};

struct TranscriptionEvent {
    int event_index;
    int chunk_index;
    std::string event_type;
    double start_seconds;
    double end_seconds;
    std::string text;
    double confidence;
};

struct TranscriptionResult {
    AudioAnalysisResult audio_analysis;
    std::vector<TranscriptChunk> transcript_segments;
    std::vector<TranscriptionEvent> transcript_events;
    std::string full_text;
    std::vector<std::string> notes;
    std::string backend_name;
    bool mock_backend;
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
TranscriptionResult TranscribeAudioBytes(
    const std::string& audio_bytes,
    const std::string& audio_label = "",
    const std::string& annotation_text = "",
    int frame_ms = 30,
    double base_energy_threshold = 0.015,
    int min_speech_ms = 240,
    int max_silence_ms = 180
);

}  // namespace meeting_copilot
