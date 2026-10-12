# ParkEasy: project spec

Status: draft. Milestone 1 (repository cleanup) is done; the rest is planned work.

## 1. Goal

A website where a visitor uploads a photo of a parking lot and gets back a clean top-down style layout of that lot: every detected space drawn as a box, green when free and red with a car icon when occupied, plus counts of free and occupied spaces.

This is the software half of the original capstone. The original system had cameras on a Raspberry Pi pushing images through RabbitMQ to a laptop, which ran the detection and wrote an image into a React page. The rebuilt version replaces the cameras and message queue with a file upload.

## 2. Scope

**In scope**

- Upload one image (JPEG or PNG) from the browser.
- Detect parking spaces and their occupancy by calling the hosted Roboflow model.
- Clean up the detections into an aligned grid.
- Show the generated layout next to the original photo, with free, occupied and total counts.
- A few bundled sample images so a visitor can try it without their own photo. These must be photos we own or that are licensed for redistribution.

**Out of scope**

- Camera capture, Raspberry Pi code, RabbitMQ, and everything else under `Embedded/` and `Raspberry_Pi/`.
- Live or periodically refreshing lots.
- Accounts, saved history, an admin page.
- Training or hosting a detection model.

## 3. What is kept from the current repository

| Keep | From | Notes |
|---|---|---|
| Roboflow inference call | `parkinglotlayout/generate-layout.py` (`scan_parking_lot`) | Own model [`ultimate-form/1`](https://universe.roboflow.com/parkeasy/ultimate-form): YOLOv8, classes `free` and `car`, 3,246 training images, mAP@50 98.8%. The script currently calls a third-party model, `parking-detection-jeremykevin/8`; see open questions. |
| Grid alignment | `parkinglotlayout/generate-layout.py` (`cleanup`, `RectangleAligner`) | Snaps box edges to shared lines within a threshold. |
| Layout drawing | `parkinglotlayout/generate-layout.py` (`draw_rectangle`, `overlay_car`), `carpng.png` | Draws boxes and the car icon on a black canvas. |

**Removed:** the original test photos (watermarked stock images, which cannot be redistributed), `Embedded/`, `Raspberry_Pi/`, `Server Image Processing/`, `attempt1.py` to `attempt6.py`, `server_script.py`, `test.py`, the committed virtualenv (`parkinglotlayout/bin`, `lib`, `lib64`, `share`, `pyvenv.cfg`), `output.txt`, `RoboFlowOutput.json`, and the Create React App project under `webapp/`.

## 4. User experience

One page, three states.

1. **Empty:** a drop zone ("Drop a parking lot photo, or choose a file") and a row of sample thumbnails.
2. **Working:** the chosen photo is shown with a progress indicator. Detection normally takes a few seconds.
3. **Result:** the original photo and the generated layout side by side (stacked on a phone), with three numbers above them: free, occupied, total. A "Try another" button returns to the empty state, and a "Download layout" button saves the PNG.

Errors are shown in place, in plain words: file too large, not an image, no parking spaces found, or the detection service is unavailable.

## 5. Architecture

```
Browser (React + Vite, static)
   │  POST /api/layout   multipart image
   ▼
API (Python, FastAPI)
   ├─ validate upload
   ├─ call Roboflow hosted inference   ← API key from environment
   ├─ align detections (RectangleAligner)
   └─ render layout PNG (OpenCV, headless)
   ▲
   │  JSON: counts, spaces, layout image
Browser renders result
```

- **Why a backend:** the Roboflow key must never reach the browser, and the alignment and drawing code is already Python.
- **Stateless:** uploads are processed in memory and not stored.
- **Hosting:** Vercel. The React build is served as a static site and the API runs as a Python function in the same project, so there is one deploy and the key lives in Vercel's environment settings. A `Dockerfile` is kept so the API can move to a container host (for example Google Cloud Run) without changes.

### API

`POST /api/layout`

- Request: `multipart/form-data` with one field, `image`.
- Limits: JPEG or PNG, 10 MB maximum, longest side resized to 1600 px before inference.
- Response `200`:

```json
{
  "counts": { "free": 12, "occupied": 30, "total": 42 },
  "image": { "width": 1280, "height": 720 },
  "spaces": [
    { "x": 104, "y": 220, "width": 60, "height": 118, "status": "free", "confidence": 0.91 }
  ],
  "layout_png": "data:image/png;base64,..."
}
```

- Errors: `400` invalid or oversized file, `422` no spaces detected, `502` Roboflow failed or timed out.

`GET /api/health` returns `200` for the host's health check.

### Layout module

The code from `generate-layout.py` moves into a small package with no side effects on import:

- `detect(image_bytes) -> list[Detection]`
- `align(detections, snap_threshold=30) -> list[Detection]`
- `render(detections, width, height) -> PNG bytes`

Returning `spaces` as data as well as the PNG keeps the option open to draw the layout as SVG in the browser later.

## 6. Fixes needed while porting

These are problems in the current code that the rebuild has to resolve.

1. **Hard-coded API key.** Done: `generate-layout.py` now reads `ROBOFLOW_API_KEY`. The old key must still be revoked in Roboflow.
2. **Desktop-only display.** `cv2.imshow` and `cv2.waitKey` need a screen. Use `opencv-python-headless` and return bytes. If the function bundle is too large for the host, the drawing can be ported to Pillow.
3. **Box position.** Roboflow returns the centre of each box, but `draw_rectangle` treats `x` as the right edge and draws from `x - width` to `x`, so the layout is shifted left by half a box. Draw from `x - width/2` to `x + width/2`.
4. **Broken debug write.** `"\n".join(result)` on a dictionary writes only its keys to `output.txt`. Remove it with the other debug prints and file writes.
5. **Fragile colour check.** The car icon is added when `color == (0, 0, 255)`. Pass the status instead.
6. **No failure handling.** Add a timeout and one retry on the Roboflow call, and handle an empty prediction list.

## 7. Security and privacy

- API key only in server environment variables; `.env` ignored by git; `.env.example` committed.
- Validate uploads by decoding them as images, not by file extension.
- Rate limit the endpoint (for example 10 requests per minute per IP), since every request spends Roboflow quota.
- CORS restricted to the site's own origin.
- Uploaded photos are sent to Roboflow for inference and are not stored by the site. Say so on the page.

## 8. Repository layout

```
ParkEasy/
├─ api/
│  ├─ index.py         FastAPI app (Vercel entry point)
│  ├─ parkeasy/        detect.py, align.py, render.py
│  ├─ assets/carpng.png
│  ├─ tests/
│  └─ pyproject.toml
├─ web/                React + Vite + TypeScript
├─ samples/            a few licensed sample photos
├─ .env.example
├─ .gitignore
├─ Dockerfile
├─ LICENSE
└─ README.md
```

## 9. Testing

- **Alignment:** unit tests on `RectangleAligner` with hand-made boxes (edges within the threshold snap together; edges outside it do not move).
- **Rendering:** given fixed detections, the PNG has the expected size and the expected pixel colours at box centres.
- **API:** tests with the Roboflow call mocked, covering success, bad file, oversized file, empty result and upstream failure.
- **CI:** GitHub Actions running the Python tests, the frontend type-check and a build on every push.

No test calls the real Roboflow service.

## 10. Milestones

1. **Clean the repository.** Done: fresh history containing only the layout code, key removed, `.gitignore`, requirements and README added.
2. **Layout package.** Port `generate-layout.py` into `detect`, `align`, `render` with the fixes in section 6 and unit tests.
3. **API.** FastAPI endpoint, validation, error handling, mocked tests.
4. **Frontend.** Upload page with the three states and sample images.
5. **Deploy.** Vercel project, key set as an environment variable, rate limit on.

## 11. Open questions

1. **Which model.** The script calls `parking-detection-jeremykevin/8`, not the project's own `ultimate-form/1`. Both use the classes `free` and `car`. Compare them on a few photos and settle on one; the last commit message says the API was "still finicky".
2. **Sample photos.** Source three or four aerial parking-lot photos that are your own or freely licensed.
3. **License.** None chosen yet.
