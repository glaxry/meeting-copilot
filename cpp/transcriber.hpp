#pragma once

#include <string>

namespace meeting_copilot {

struct RuntimeInfo {
    std::string backend;
    std::string version;
    std::string compiler;
};

RuntimeInfo GetRuntimeInfo();
std::string DescribeAudio(int sample_rate_hz, int frame_count);

}  // namespace meeting_copilot
