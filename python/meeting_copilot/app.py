from fastapi import FastAPI

from meeting_copilot.bridge import get_cpp_runtime_info
from meeting_copilot.config import get_settings
from meeting_copilot.routers.transcribe import router as transcribe_router
from meeting_copilot.schemas import HealthResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Day2 native audio pipeline for the Meeting Copilot project.",
)
app.include_router(transcribe_router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    cpp_runtime_info = get_cpp_runtime_info()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        cpp_backend_available=cpp_runtime_info is not None,
        cpp_backend=cpp_runtime_info,
    )
