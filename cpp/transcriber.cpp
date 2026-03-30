#include "transcriber.hpp"

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
    info.backend = "day1-native-skeleton";
    info.version = "0.1.0";
    info.compiler = DetectCompiler();
    return info;
}

std::string DescribeAudio(const int sample_rate_hz, const int frame_count) {
    std::ostringstream builder;
    builder << "Audio frames: " << frame_count << " @ " << sample_rate_hz << " Hz";
    return builder.str();
}

}  // namespace meeting_copilot
