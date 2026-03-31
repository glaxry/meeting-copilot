#include "audio_preprocess.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace meeting_copilot {

namespace {

std::uint16_t ReadUInt16(const std::string& bytes, const std::size_t offset) {
    const auto low = static_cast<std::uint8_t>(bytes.at(offset));
    const auto high = static_cast<std::uint8_t>(bytes.at(offset + 1));
    return static_cast<std::uint16_t>(low | (high << 8));
}

std::uint32_t ReadUInt32(const std::string& bytes, const std::size_t offset) {
    const auto byte0 = static_cast<std::uint8_t>(bytes.at(offset));
    const auto byte1 = static_cast<std::uint8_t>(bytes.at(offset + 1));
    const auto byte2 = static_cast<std::uint8_t>(bytes.at(offset + 2));
    const auto byte3 = static_cast<std::uint8_t>(bytes.at(offset + 3));
    return static_cast<std::uint32_t>(byte0 | (byte1 << 8) | (byte2 << 16) | (byte3 << 24));
}

double ComputeFrameEnergy(
    const std::vector<std::int16_t>& samples,
    const int channels,
    const int start_frame,
    const int end_frame
) {
    if (end_frame <= start_frame) {
        return 0.0;
    }

    double squared_sum = 0.0;
    std::size_t sample_count = 0;

    for (int frame = start_frame; frame < end_frame; ++frame) {
        for (int channel = 0; channel < channels; ++channel) {
            const auto sample = static_cast<double>(samples.at(frame * channels + channel));
            squared_sum += sample * sample;
            ++sample_count;
        }
    }

    if (sample_count == 0) {
        return 0.0;
    }

    return std::sqrt(squared_sum / static_cast<double>(sample_count)) / 32768.0;
}

}  // namespace

WaveAudio DecodeWaveBytes(const std::string& audio_bytes) {
    if (audio_bytes.size() < 44) {
        throw std::runtime_error("WAV payload is too small to contain a valid header.");
    }

    if (audio_bytes.compare(0, 4, "RIFF") != 0 || audio_bytes.compare(8, 4, "WAVE") != 0) {
        throw std::runtime_error("Only RIFF/WAVE audio is supported.");
    }

    std::uint16_t audio_format = 0;
    std::uint16_t channels = 0;
    std::uint32_t sample_rate_hz = 0;
    std::uint16_t bits_per_sample = 0;
    std::size_t data_offset = 0;
    std::size_t data_size = 0;

    std::size_t offset = 12;
    while (offset + 8 <= audio_bytes.size()) {
        const auto chunk_id = audio_bytes.substr(offset, 4);
        const auto chunk_size = static_cast<std::size_t>(ReadUInt32(audio_bytes, offset + 4));
        const auto chunk_data = offset + 8;

        if (chunk_data + chunk_size > audio_bytes.size()) {
            throw std::runtime_error("Encountered a truncated WAV chunk.");
        }

        if (chunk_id == "fmt ") {
            if (chunk_size < 16) {
                throw std::runtime_error("WAV fmt chunk is too small.");
            }
            audio_format = ReadUInt16(audio_bytes, chunk_data);
            channels = ReadUInt16(audio_bytes, chunk_data + 2);
            sample_rate_hz = ReadUInt32(audio_bytes, chunk_data + 4);
            bits_per_sample = ReadUInt16(audio_bytes, chunk_data + 14);
        } else if (chunk_id == "data") {
            data_offset = chunk_data;
            data_size = chunk_size;
        }

        offset = chunk_data + chunk_size + (chunk_size % 2);
    }

    if (audio_format != 1) {
        throw std::runtime_error("Only PCM WAV files are supported.");
    }
    if (channels == 0 || sample_rate_hz == 0) {
        throw std::runtime_error("WAV fmt metadata is incomplete.");
    }
    if (bits_per_sample != 16) {
        throw std::runtime_error("Only 16-bit PCM WAV files are supported.");
    }
    if (data_offset == 0 || data_size == 0) {
        throw std::runtime_error("WAV file does not contain a data chunk.");
    }
    if (data_size % sizeof(std::int16_t) != 0) {
        throw std::runtime_error("WAV data chunk is not aligned to 16-bit samples.");
    }

    std::vector<std::int16_t> samples;
    samples.reserve(data_size / sizeof(std::int16_t));
    for (std::size_t index = 0; index < data_size; index += sizeof(std::int16_t)) {
        const auto sample_offset = data_offset + index;
        samples.push_back(static_cast<std::int16_t>(ReadUInt16(audio_bytes, sample_offset)));
    }

    if (samples.size() % channels != 0) {
        throw std::runtime_error("WAV sample data does not divide evenly by channel count.");
    }

    const auto frame_count = static_cast<int>(samples.size() / channels);
    const auto duration_seconds = frame_count == 0
        ? 0.0
        : static_cast<double>(frame_count) / static_cast<double>(sample_rate_hz);

    return WaveAudio{
        static_cast<int>(sample_rate_hz),
        static_cast<int>(channels),
        frame_count,
        duration_seconds,
        std::move(samples),
    };
}

std::vector<VoiceFrameDecision> DetectVoiceFrames(
    const WaveAudio& audio,
    const int frame_ms,
    const double base_energy_threshold
) {
    if (frame_ms <= 0) {
        throw std::runtime_error("frame_ms must be positive.");
    }

    const auto samples_per_frame = std::max(1, audio.sample_rate_hz * frame_ms / 1000);
    std::vector<VoiceFrameDecision> frames;

    double max_energy = 0.0;
    for (int start_frame = 0; start_frame < audio.frame_count; start_frame += samples_per_frame) {
        const auto end_frame = std::min(audio.frame_count, start_frame + samples_per_frame);
        const auto energy = ComputeFrameEnergy(audio.samples, audio.channels, start_frame, end_frame);
        max_energy = std::max(max_energy, energy);
        frames.push_back(VoiceFrameDecision{
            start_frame,
            end_frame,
            static_cast<double>(start_frame) / static_cast<double>(audio.sample_rate_hz),
            static_cast<double>(end_frame) / static_cast<double>(audio.sample_rate_hz),
            energy,
            false,
        });
    }

    // Keep the threshold adaptive so a quiet file can still produce speech
    // windows, while obvious silence remains below the decision boundary.
    const auto effective_threshold = std::max(base_energy_threshold, max_energy * 0.18);
    for (auto& frame : frames) {
        frame.speech = frame.energy >= effective_threshold;
    }

    return frames;
}

}  // namespace meeting_copilot
