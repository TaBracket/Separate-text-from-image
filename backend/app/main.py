from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from .schemas import DetectResponse
from .processing import detect_dark_item, overlay_png_bytes

app = FastAPI(title="Dark-Item Detector (High-Contrast)", version="1.0.0")

# در توسعه باز؛ در دیپلوی محدود کن
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/detect", response_model=DetectResponse)
async def detect_api(
    file: UploadFile = File(...),
    target_width: int = Query(960, ge=200, le=4000),
    blur_kernel: int = Query(5, ge=1, le=51),
    min_area_ratio: float = Query(0.005, ge=0.0, le=0.5),
    max_area_ratio: float = Query(0.90, ge=0.1, le=1.0),
    edge_penalty: float = Query(0.8, ge=0.0, le=1.0),
    approx_eps: float = Query(2.0, ge=0.0, le=20.0),
):
    if "image" not in (file.content_type or ""):
        raise HTTPException(status_code=400, detail="Please upload an image/*")

    data = await file.read()
    try:
        res = detect_dark_item(
            data,
            target_width=target_width,
            blur_kernel=blur_kernel,
            min_area_ratio=min_area_ratio,
            max_area_ratio=max_area_ratio,
            edge_penalty=edge_penalty,
            approx_eps=approx_eps,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "width": res["width"],
        "height": res["height"],
        "item": res["item"],
    }

@app.post("/detect/overlay")
async def detect_overlay_api(
    file: UploadFile = File(...),
    target_width: int = Query(960, ge=200, le=4000),
    blur_kernel: int = Query(5, ge=1, le=51),
    min_area_ratio: float = Query(0.005, ge=0.0, le=0.5),
    max_area_ratio: float = Query(0.90, ge=0.1, le=1.0),
    edge_penalty: float = Query(0.8, ge=0.0, le=1.0),
    approx_eps: float = Query(2.0, ge=0.0, le=20.0),
):
    if "image" not in (file.content_type or ""):
        raise HTTPException(status_code=400, detail="Please upload an image/*")

    data = await file.read()
    res = detect_dark_item(
        data,
        target_width=target_width,
        blur_kernel=blur_kernel,
        min_area_ratio=min_area_ratio,
        max_area_ratio=max_area_ratio,
        edge_penalty=edge_penalty,
        approx_eps=approx_eps,
    )
    png = overlay_png_bytes(res["overlay"])
    return Response(content=png, media_type="image/png")
