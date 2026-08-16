"""Replaceable desktop OCR boundary; manual entry is always available."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class OCRProvider(Protocol):
    name: str

    def available(self) -> bool: ...

    def extract(self, image_path: Path) -> str: ...


class ManualOCRProvider:
    name = "manual"

    def available(self) -> bool:
        return True

    def extract(self, image_path: Path) -> str:
        raise RuntimeError(f"manual entry required for {image_path.name}")


class AppleVisionOCRProvider:
    name = "apple-vision"

    def available(self) -> bool:
        try:
            import Quartz  # noqa: F401
            import Vision  # noqa: F401
        except ImportError:
            return False
        return True

    def extract(self, image_path: Path) -> str:
        if not self.available():
            raise RuntimeError("Apple Vision OCR requires the optional apple-ocr dependencies")
        import Quartz
        import Vision

        url = Quartz.CFURLCreateFromFileSystemRepresentation(
            None, str(image_path).encode(), len(str(image_path).encode()), False
        )
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
        success, error = handler.performRequests_error_([request], None)
        if not success:
            raise RuntimeError(f"Apple Vision OCR failed: {error}")
        return "\n".join(
            candidate.string()
            for observation in request.results() or []
            if (candidate := observation.topCandidates_(1).firstObject()) is not None
        )
