export interface OCRProgress {
  status: string;
  progress: number;
}

export async function extractEstimateText(file: File, onProgress?: (progress: OCRProgress) => void) {
  const { createWorker } = await import("tesseract.js");
  const worker = await createWorker("eng", 1, {
    workerPath: "/ocr/worker.min.js",
    corePath: "/ocr/core",
    langPath: "/ocr/lang",
    cacheMethod: "write",
    logger: (message) => onProgress?.({ status: message.status, progress: message.progress }),
  });
  try {
    const result = await worker.recognize(file);
    return result.data.text;
  } finally {
    await worker.terminate();
  }
}
