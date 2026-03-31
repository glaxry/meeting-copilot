#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace meeting_copilot {

struct WaveAudio {
    int sample_rate_hz;
    int channels;
    int frame_count;
    double duration_seconds;
    std::vector<std::int16_t> samples;
};

struct VoiceFrameDecision {
    int start_sample;
    int end_sample;
    double start_seconds;
    double end_seconds;
    double energy;
    bool speech;
};

WaveAudio DecodeWaveBytes(const std::string& audio_bytes);
std::vector<VoiceFrameDecision> DetectVoiceFrames(
    const WaveAudio& audio,
    int frame_ms,
    double base_energy_threshold
);

}  // namespace meeting_copilot
