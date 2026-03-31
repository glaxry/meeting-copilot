#include <pybind11/pybind11.h>

#include "transcriber.hpp"

namespace py = pybind11;

PYBIND11_MODULE(meeting_copilot_cpp, module) {
    module.doc() = "Day2 pybind11 audio pipeline for Meeting Copilot";

    module.def("runtime_info", []() {
        const auto info = meeting_copilot::GetRuntimeInfo();
        py::dict data;
        data["backend"] = info.backend;
        data["version"] = info.version;
        data["compiler"] = info.compiler;
        return data;
    });

    module.def(
        "describe_audio",
        &meeting_copilot::DescribeAudio,
        py::arg("sample_rate_hz"),
        py::arg("frame_count")
    );

    module.def(
        "analyze_audio_bytes",
        [](py::bytes audio_bytes, const int frame_ms, const double energy_threshold, const int min_speech_ms, const int max_silence_ms) {
            const std::string raw_bytes = audio_bytes;
            const auto result = meeting_copilot::AnalyzeAudioBytes(
                raw_bytes,
                frame_ms,
                energy_threshold,
                min_speech_ms,
                max_silence_ms
            );

            py::list speech_segments;
            for (const auto& segment : result.speech_segments) {
                py::dict item;
                item["start_seconds"] = segment.start_seconds;
                item["end_seconds"] = segment.end_seconds;
                item["frame_count"] = segment.frame_count;
                item["sample_count"] = segment.sample_count;
                item["average_energy"] = segment.average_energy;
                speech_segments.append(item);
            }

            py::dict payload;
            payload["sample_rate_hz"] = result.sample_rate_hz;
            payload["channels"] = result.channels;
            payload["total_frame_count"] = result.total_frame_count;
            payload["duration_seconds"] = result.duration_seconds;
            payload["speech_duration_seconds"] = result.speech_duration_seconds;
            payload["speech_segments"] = speech_segments;
            return payload;
        },
        py::arg("audio_bytes"),
        py::arg("frame_ms") = 30,
        py::arg("energy_threshold") = 0.015,
        py::arg("min_speech_ms") = 240,
        py::arg("max_silence_ms") = 180
    );
}
