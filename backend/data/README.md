# SafetyLens local media directories

Place short demonstration workplace videos in this tree only for local development.

Recommended location for source demos (not used by the API automatically):

```text
backend/data/demo-source/
```

Runtime directories created automatically by the API:

- `uploads/` — stored uploaded videos (UUID filenames)
- `frames/` — extracted JPEG evidence-candidate frames
- `procedures/` — uploaded company procedure originals (PDF/TXT/MD)

## Guidelines

- Prefer short MP4 clips (10–30 seconds).
- Supported formats: MP4, MOV, WebM.
- Procedure uploads: PDF, TXT, Markdown (size limits in `.env`).
- Maximum size and duration are configured in `.env`.
- Do not commit uploaded videos, frames, or private procedures.
- Do not place copyrighted media in the repository.

If no demo video is available, the application remains functional and shows an empty upload state.
