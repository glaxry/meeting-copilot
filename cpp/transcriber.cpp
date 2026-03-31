#include "transcriber.hpp"

#include "audio_preprocess.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

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

double SegmentConfidence(const double average_energy) {
    const auto confidence = 0.55 + average_energy * 4.0;
    return std::max(0.2, std::min(0.99, confidence));
}

std::string NormalizeWhitespace(const std::string& text) {
    std::string normalized;
    normalized.reserve(text.size());

    bool last_was_space = true;
    for (const char character : text) {
        const auto is_space = std::isspace(static_cast<unsigned char>(character)) != 0;
        if (is_space) {
            if (!last_was_space) {
                normalized.push_back(' ');
            }
        } else {
            normalized.push_back(character);
        }
        last_was_space = is_space;
    }

    if (!normalized.empty() && normalized.back() == ' ') {
        normalized.pop_back();
    }
    return normalized;
}

std::vector<std::string> SplitWords(const std::string& text) {
    std::istringstream reader(text);
    std::vector<std::string> words;
    std::string word;
    while (reader >> word) {
        words.push_back(word);
    }
    return words;
}

std::string JoinStrings(const std::vector<std::string>& items, const std::string& delimiter) {
    if (items.empty()) {
        return "";
    }

    std::ostringstream builder;
    for (std::size_t index = 0; index < items.size(); ++index) {
        if (index > 0) {
            builder << delimiter;
        }
        builder << items.at(index);
    }
    return builder.str();
}

std::size_t MaxChunkCount(const std::string& transcript_text) {
    const auto normalized = NormalizeWhitespace(transcript_text);
    const auto words = SplitWords(normalized);
    if (!words.empty()) {
        return words.size();
    }
    return std::max<std::size_t>(1, normalized.size());
}

std::vector<std::string> SplitTextIntoChunks(const std::string& transcript_text, const std::size_t segment_count) {
    const auto normalized = NormalizeWhitespace(transcript_text);
    if (segment_count <= 1 || normalized.empty()) {
        return {normalized};
    }

    const auto words = SplitWords(normalized);
    std::vector<std::string> chunks;
    chunks.reserve(segment_count);

    if (words.size() >= segment_count) {
        for (std::size_t index = 0; index < segment_count; ++index) {
            const auto start = static_cast<std::size_t>(std::llround(
                static_cast<double>(index) * static_cast<double>(words.size()) / static_cast<double>(segment_count)
            ));
            const auto end = static_cast<std::size_t>(std::llround(
                static_cast<double>(index + 1) * static_cast<double>(words.size()) / static_cast<double>(segment_count)
            ));

            std::vector<std::string> bucket(words.begin() + start, words.begin() + end);
            auto chunk = JoinStrings(bucket, " ");
            if (chunk.empty()) {
                chunk = chunks.empty() ? normalized : chunks.back();
            }
            chunks.push_back(chunk);
        }
        return chunks;
    }

    std::vector<std::string> characters;
    characters.reserve(normalized.size());
    for (const char character : normalized) {
        characters.emplace_back(1, character);
    }

    for (std::size_t index = 0; index < segment_count; ++index) {
        const auto start = static_cast<std::size_t>(std::llround(
            static_cast<double>(index) * static_cast<double>(characters.size()) / static_cast<double>(segment_count)
        ));
        const auto end = static_cast<std::size_t>(std::llround(
            static_cast<double>(index + 1) * static_cast<double>(characters.size()) / static_cast<double>(segment_count)
        ));

        std::vector<std::string> bucket(characters.begin() + start, characters.begin() + end);
        auto chunk = JoinStrings(bucket, "");
        if (chunk.empty()) {
            chunk = chunks.empty() ? normalized : chunks.back();
        }
        chunks.push_back(chunk);
    }

    return chunks;
}

std::vector<SpeechSegment> MergeSegments(const std::vector<SpeechSegment>& segments, const std::size_t target_count) {
    if (target_count >= segments.size()) {
        return segments;
    }

    std::vector<SpeechSegment> merged;
    merged.reserve(target_count);

    for (std::size_t index = 0; index < target_count; ++index) {
        const auto start = static_cast<std::size_t>(std::llround(
            static_cast<double>(index) * static_cast<double>(segments.size()) / static_cast<double>(target_count)
        ));
        const auto end = static_cast<std::size_t>(std::llround(
            static_cast<double>(index + 1) * static_cast<double>(segments.size()) / static_cast<double>(target_count)
        ));

        if (start >= end) {
            continue;
        }

        const auto bucket_begin = segments.begin() + static_cast<std::ptrdiff_t>(start);
        const auto bucket_end = segments.begin() + static_cast<std::ptrdiff_t>(end);

        int total_frames = 0;
        int total_samples = 0;
        double total_energy = 0.0;
        int energy_count = 0;
        for (auto iterator = bucket_begin; iterator != bucket_end; ++iterator) {
            total_frames += iterator->frame_count;
            total_samples += iterator->sample_count;
            total_energy += iterator->average_energy;
            ++energy_count;
        }

        merged.push_back(SpeechSegment{
            bucket_begin->start_seconds,
            (bucket_end - 1)->end_seconds,
            total_frames,
            total_samples,
            energy_count == 0 ? 0.0 : total_energy / static_cast<double>(energy_count),
        });
    }

    return merged;
}

std::vector<SpeechSegment> BuildDisplaySegments(const AudioAnalysisResult& analysis) {
    if (!analysis.speech_segments.empty()) {
        return analysis.speech_segments;
    }
    if (analysis.duration_seconds <= 0.0) {
        return {};
    }

    return {
        SpeechSegment{
            0.0,
            analysis.duration_seconds,
            analysis.total_frame_count,
            analysis.total_frame_count * analysis.channels,
            0.0,
        }
    };
}

std::string BuildMockText(
    const std::string& audio_label,
    const int segment_index,
    const SpeechSegment& segment
) {
    std::ostringstream builder;
    builder << "Day3 mock speech segment " << segment_index + 1;
    if (!audio_label.empty()) {
        builder << " for '" << audio_label << "'";
    }
    builder << " from " << std::fixed;
    builder.precision(2);
    builder << segment.start_seconds << "s to " << segment.end_seconds << "s.";
    return builder.str();
}

std::string BuildPartialText(const std::string& text) {
    const auto normalized = NormalizeWhitespace(text);
    if (normalized.empty()) {
        return normalized;
    }

    const auto words = SplitWords(normalized);
    if (words.size() > 1) {
        const auto partial_word_count = std::max<std::size_t>(1, words.size() / 2);
        std::vector<std::string> partial_words(words.begin(), words.begin() + static_cast<std::ptrdiff_t>(partial_word_count));
        return JoinStrings(partial_words, " ");
    }

    if (normalized.size() == 1) {
        return normalized;
    }

    return normalized.substr(0, std::max<std::size_t>(1, normalized.size() / 2));
}

}  // namespace

RuntimeInfo GetRuntimeInfo() {
    RuntimeInfo info;
    info.backend = "day3-native-transcription-bridge";
    info.version = "0.3.0";
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

    // Group speech frames while tolerating short silence gaps, which keeps nearby
    // speech frames in the same segment instead of fragmenting every pause.
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

TranscriptionResult TranscribeAudioBytes(
    const std::string& audio_bytes,
    const std::string& audio_label,
    const std::string& annotation_text,
    const int frame_ms,
    const double base_energy_threshold,
    const int min_speech_ms,
    const int max_silence_ms
) {
    auto analysis = AnalyzeAudioBytes(
        audio_bytes,
        frame_ms,
        base_energy_threshold,
        min_speech_ms,
        max_silence_ms
    );

    auto display_segments = BuildDisplaySegments(analysis);
    const auto normalized_annotation = NormalizeWhitespace(annotation_text);
    const auto mock_backend = normalized_annotation.empty();
    std::vector<std::string> notes;

    if (analysis.speech_segments.empty()) {
        notes.push_back("Day3 did not detect voiced speech windows, so transcript output uses the full audio span.");
    }

    if (!mock_backend) {
        notes.push_back("Day3 native transcriber distributed annotation text across the detected speech windows.");
        const auto target_chunk_count = std::max<std::size_t>(1, std::min(display_segments.size(), MaxChunkCount(normalized_annotation)));
        if (target_chunk_count < display_segments.size()) {
            display_segments = MergeSegments(display_segments, target_chunk_count);
        }
    } else {
        notes.push_back("Day3 native transcriber generated mock transcript text because no annotation text was provided.");
    }

    std::vector<std::string> text_chunks;
    if (!display_segments.empty()) {
        if (!mock_backend) {
            text_chunks = SplitTextIntoChunks(normalized_annotation, display_segments.size());
        } else {
            text_chunks.reserve(display_segments.size());
            for (std::size_t index = 0; index < display_segments.size(); ++index) {
                text_chunks.push_back(BuildMockText(audio_label, static_cast<int>(index), display_segments.at(index)));
            }
        }
    }

    std::vector<TranscriptChunk> transcript_segments;
    transcript_segments.reserve(display_segments.size());

    for (std::size_t index = 0; index < display_segments.size(); ++index) {
        const auto& segment = display_segments.at(index);
        transcript_segments.push_back(TranscriptChunk{
            static_cast<int>(index),
            segment.start_seconds,
            segment.end_seconds,
            text_chunks.at(index),
            SegmentConfidence(segment.average_energy),
        });
    }

    std::vector<TranscriptionEvent> transcript_events;
    transcript_events.reserve(transcript_segments.size() * 2);

    int event_index = 0;
    for (const auto& chunk : transcript_segments) {
        const auto duration_seconds = std::max(0.0, chunk.end_seconds - chunk.start_seconds);
        const auto midpoint_seconds = chunk.start_seconds + duration_seconds * 0.6;
        const auto partial_text = BuildPartialText(chunk.text);

        transcript_events.push_back(TranscriptionEvent{
            event_index++,
            chunk.chunk_index,
            "partial",
            chunk.start_seconds,
            midpoint_seconds,
            partial_text,
            chunk.confidence,
        });
        transcript_events.push_back(TranscriptionEvent{
            event_index++,
            chunk.chunk_index,
            "final",
            chunk.start_seconds,
            chunk.end_seconds,
            chunk.text,
            chunk.confidence,
        });
    }

    std::vector<std::string> final_text_chunks;
    final_text_chunks.reserve(transcript_segments.size());
    for (const auto& chunk : transcript_segments) {
        final_text_chunks.push_back(chunk.text);
    }

    std::ostringstream event_note;
    event_note << "Day3 native bridge emitted " << transcript_events.size() << " incremental transcription event(s).";
    notes.push_back(event_note.str());

    return TranscriptionResult{
        std::move(analysis),
        std::move(transcript_segments),
        std::move(transcript_events),
        JoinStrings(final_text_chunks, " "),
        std::move(notes),
        "cpp-day3-pybind",
        mock_backend,
    };
}

}  // namespace meeting_copilot
