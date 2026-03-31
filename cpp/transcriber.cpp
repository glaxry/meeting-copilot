#include "transcriber.hpp"

#include "audio_preprocess.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

namespace meeting_copilot {

namespace {

std::string DetectCompiler() {
#if defined(_MSC_VER)
    return "MSVC";
#elif defined(__clang__)
    return "Clang";
#elif defined(__GNUC__)
    return "GCC";
#else
    return "Unknown";
#endif
}

}  // namespace

RuntimeInfo GetRuntimeInfo() {
    RuntimeInfo info;
    info.backend = "day2-native-audio-pipeline";
    info.version = "0.2.0";
    info.compiler = DetectCompiler();
    return info;
}

std::string DescribeAudio(const int sample_rate_hz, const int frame_count) {
    std::ostringstream builder;
    builder << "Audio frames: " << frame_count << " @ " << sample_rate_hz << " Hz";
    return builder.str();
}

AudioAnalysisResult AnalyzeAudioBytes(
    const std::string& audio_bytes,
    const int frame_ms,
    const double base_energy_threshold,
    const int min_speech_ms,
    const int max_silence_ms
) {
    const auto audio = DecodeWaveBytes(audio_bytes);
    const auto voice_frames = DetectVoiceFrames(audio, frame_ms, base_energy_threshold);

    const auto min_speech_frames = std::max(1, static_cast<int>(std::ceil(
        static_cast<double>(min_speech_ms) / static_cast<double>(frame_ms)
    )));
    const auto max_silence_frames = std::max(0, max_silence_ms / frame_ms);

    std::vector<SpeechSegment> speech_segments;
    int segment_start_index = -1;
    int last_speech_index = -1;
    int speech_frame_count = 0;
    double speech_energy_sum = 0.0;

    // Group speech frames while tolerating short silence gaps, which keeps nearby
    // speech frames in the same segment instead of fragmenting every pause.
    const auto flush_segment = [&](const int end_index) {
        if (segment_start_index < 0 || last_speech_index < 0) {
            return;
        }
        if (speech_frame_count < min_speech_frames) {
            return;
        }

        const auto& first_frame = voice_frames.at(segment_start_index);
        const auto& last_frame = voice_frames.at(end_index);
        speech_segments.push_back(SpeechSegment{
            first_frame.start_seconds,
            last_frame.end_seconds,
            end_index - segment_start_index + 1,
            (last_frame.end_sample - first_frame.start_sample) * audio.channels,
            speech_energy_sum / static_cast<double>(speech_frame_count),
        });
    };

    for (int index = 0; index < static_cast<int>(voice_frames.size()); ++index) {
        const auto& frame = voice_frames.at(index);
        if (frame.speech) {
            if (segment_start_index < 0) {
                segment_start_index = index;
            }
            last_speech_index = index;
            ++speech_frame_count;
            speech_energy_sum += frame.energy;
            continue;
        }

        if (segment_start_index >= 0 && last_speech_index >= 0 && index - last_speech_index > max_silence_frames) {
            flush_segment(last_speech_index);
            segment_start_index = -1;
            last_speech_index = -1;
            speech_frame_count = 0;
            speech_energy_sum = 0.0;
        }
    }

    if (segment_start_index >= 0 && last_speech_index >= 0) {
        flush_segment(last_speech_index);
    }

    double speech_duration_seconds = 0.0;
    for (const auto& segment : speech_segments) {
        speech_duration_seconds += segment.end_seconds - segment.start_seconds;
    }

    return AudioAnalysisResult{
        audio.sample_rate_hz,
        audio.channels,
        audio.frame_count,
        audio.duration_seconds,
        speech_duration_seconds,
        std::move(speech_segments),
    };
}

}  // namespace meeting_copilot
