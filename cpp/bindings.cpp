#include <pybind11/pybind11.h>

#include "transcriber.hpp"

namespace py = pybind11;

PYBIND11_MODULE(meeting_copilot_cpp, module) {
    module.doc() = "Day1 pybind11 skeleton for Meeting Copilot";

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
}
