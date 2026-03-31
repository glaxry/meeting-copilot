#include <pybind11/pybind11.h>

#include "transcriber.hpp"

namespace py = pybind11;

PYBIND11_MODULE(meeting_copilot_cpp, module) {
    module.doc() = "Day3 pybind11 transcription bridge for Meeting Copilot";

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

    module.def(
        "transcribe_audio_bytes",
        [](py::bytes audio_bytes,
           const std::string& audio_label,
           const std::string& annotation_text,
           const int frame_ms,
           const double energy_threshold,
           const int min_speech_ms,
           const int max_silence_ms) {
            const std::string raw_bytes = audio_bytes;
            const auto result = meeting_copilot::TranscribeAudioBytes(
                raw_bytes,
                audio_label,
                annotation_text,
                frame_ms,
                energy_threshold,
                min_speech_ms,
                max_silence_ms
            );

            py::list speech_segments;
            for (const auto& segment : result.audio_analysis.speech_segments) {
                py::dict item;
                item["start_seconds"] = segment.start_seconds;
                item["end_seconds"] = segment.end_seconds;
                item["frame_count"] = segment.frame_count;
                item["sample_count"] = segment.sample_count;
                item["average_energy"] = segment.average_energy;
                speech_segments.append(item);
            }

            py::list transcript_segments;
            for (const auto& segment : result.transcript_segments) {
                py::dict item;
                item["chunk_index"] = segment.chunk_index;
                item["start_seconds"] = segment.start_seconds;
                item["end_seconds"] = segment.end_seconds;
                item["text"] = segment.text;
                item["confidence"] = segment.confidence;
                transcript_segments.append(item);
            }

            py::list transcript_events;
            for (const auto& event : result.transcript_events) {
                py::dict item;
                item["event_index"] = event.event_index;
                item["chunk_index"] = event.chunk_index;
                item["event_type"] = event.event_type;
                item["start_seconds"] = event.start_seconds;
                item["end_seconds"] = event.end_seconds;
                item["text"] = event.text;
                item["confidence"] = event.confidence;
                transcript_events.append(item);
            }

            py::list notes;
            for (const auto& note : result.notes) {
                notes.append(note);
            }

            py::dict payload;
            payload["sample_rate_hz"] = result.audio_analysis.sample_rate_hz;
            payload["channels"] = result.audio_analysis.channels;
            payload["total_frame_count"] = result.audio_analysis.total_frame_count;
            payload["duration_seconds"] = result.audio_analysis.duration_seconds;
            payload["speech_duration_seconds"] = result.audio_analysis.speech_duration_seconds;
            payload["speech_segments"] = speech_segments;
            payload["transcript_segments"] = transcript_segments;
            payload["transcript_events"] = transcript_events;
            payload["full_text"] = result.full_text;
            payload["notes"] = notes;
            payload["backend_name"] = result.backend_name;
            payload["mock_backend"] = result.mock_backend;
            return payload;
        },
        py::arg("audio_bytes"),
        py::arg("audio_label") = "",
        py::arg("annotation_text") = "",
        py::arg("frame_ms") = 30,
        py::arg("energy_threshold") = 0.015,
        py::arg("min_speech_ms") = 240,
        py::arg("max_silence_ms") = 180
    );
}
