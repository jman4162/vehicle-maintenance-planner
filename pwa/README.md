# Offline PWA

This Vite/React PWA is a static, backend-free appointment companion. It stores only AES-GCM
ciphertext in Dexie/IndexedDB, validates imported packets with Zod, bundles Tesseract.js worker,
core, and English data locally, and precaches the application with Workbox.

```bash
npm ci
npm test
npm run build
npm run test:offline
```

Do not add analytics, telemetry, remote fonts, runtime CDN dependencies, or network-backed
storage. Estimate images are passed directly to the local OCR worker and are not persisted;
the file input is cleared after extraction. Hosting remains blocked until every item in
`../RELEASE.md` passes.
