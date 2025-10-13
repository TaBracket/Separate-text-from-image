import cv2
import numpy as np
from typing import Dict, Tuple

# ---------- helpers ----------

def _resize_to_width(img: np.ndarray, target_w: int) -> Tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    scale = target_w / float(w)
    target_h = int(round(h * scale))
    resized = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_AREA)
    return resized, scale

def _luminance_lab(img_bgr: np.ndarray) -> np.ndarray:
    """
    روشنایی پایدارتر نسبت به Gray ساده: LAB + CLAHE برای مقابله با نور ناهمگن.
    خروجی: uint8 با بازه 0..255 (تاریک=کوچک‌تر)
    """
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    Lc = clahe.apply(L)
    return Lc

def _binary_dark_mask(Lc_blur: np.ndarray) -> np.ndarray:
    """
    ماسک دودویی نواحی «تاریک» (foreground):
    - آستانه‌گذاری Otsu با THRESH_BINARY_INV
    - ادغام با آستانه درصدی (مثلاً p20) برای پایداری در تصاویر خاص
    """
    # Otsu (معکوس) → پیکسل‌های تاریک سفید می‌شوند
    _, m_otsu = cv2.threshold(Lc_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # آستانهٔ درصدی: پایین‌ترین 20 درصد شدت‌ها را هم تاریک حساب کن
    p20 = np.percentile(Lc_blur, 20)
    _, m_pct = cv2.threshold(Lc_blur, int(p20), 255, cv2.THRESH_BINARY_INV)

    mask = cv2.bitwise_or(m_otsu, m_pct)
    return mask

def _postproc_mask(mask: np.ndarray) -> np.ndarray:
    """
    تمیزکاری ماسک: close برای بستن شکاف‌ها، سپس open برای حذف نویز.
    """
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k5, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3, iterations=1)
    return mask

# ---------- main pipeline ----------

def detect_dark_item(
    img_bytes: bytes,
    target_width: int = 960,
    blur_kernel: int = 5,
    min_area_ratio: float = 0.005,
    max_area_ratio: float = 0.90,
    edge_penalty: float = 0.8,
    approx_eps: float = 2.0,
) -> Dict:
    """
    منطق: آیتم تاریک‌تر از پس‌زمینه است.
    - تبدیل به روشنایی (LAB L) + CLAHE
    - بلور ملایم
    - آستانه‌گذاری برای تاریک‌ها
    - تمیزکاری ماسک و استخراج کانتورها
    - انتخاب «تاریک‌ترین جزء متصل معتبر» با پنالتی لبه
    """
    buf = np.frombuffer(img_bytes, np.uint8)
    src = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if src is None:
        raise ValueError("Invalid image data")

    H0, W0 = src.shape[:2]
    proc, scale = _resize_to_width(src, target_width)
    h, w = proc.shape[:2]

    # روشنایی + بلور
    Lc = _luminance_lab(proc)
    k = blur_kernel | 1
    Lb = cv2.GaussianBlur(Lc, (k, k), 0)

    # ماسک تاریک‌ها + تمیزکاری
    mask = _binary_dark_mask(Lb)
    mask = _postproc_mask(mask)

    # کانتورها
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img_area = float(w * h)

    choose = None
    best_score = -1.0
    best_rect = None
    best_meanL = 255.0
    best_edge_touch = False

    for c in cnts:
        area = cv2.contourArea(c)
        if area < img_area * min_area_ratio or area > img_area * max_area_ratio:
            continue

        x, y, ww, hh = cv2.boundingRect(c)
        edge_touch = (x <= 1 or y <= 1 or x + ww >= w - 1 or y + hh >= h - 1)

        # میانگین روشنایی داخل کانتور → تاریک‌تر = کوچک‌تر
        filled = np.zeros((h, w), np.uint8)
        cv2.drawContours(filled, [c], -1, 255, thickness=-1)
        meanL = cv2.mean(Lb, filled)[0]  # 0..255 (تاریک‌تر = کمتر)

        # امتیاز: تاریکی غالب مهم‌تر از مساحت؛
        # با sqrt(area) وزن می‌دهیم تا لکه‌های خیلی کوچک غالب نشوند.
        score = (255.0 - meanL) * (np.sqrt(area) / np.sqrt(img_area))
        if edge_touch:
            score *= edge_penalty  # پنالتی برای کانتورهای چسبیده به لبه

        if score > best_score:
            best_score = float(score)
            choose = c
            best_rect = (x, y, ww, hh)
            best_meanL = float(meanL)
            best_edge_touch = edge_touch

    overlay = proc.copy()
    result_item = None

    if choose is not None:
        # چندضلعی ساده‌شده برای کشیدن خط قرمز تمیز
        approx = cv2.approxPolyDP(choose, approx_eps, True)
        rrect = cv2.minAreaRect(choose)  # ((cx,cy),(w,h),angle)
        (cx, cy), (rw, rh), ang = rrect

        # خط قرمز دور آیتم
        cv2.polylines(overlay, [approx], True, (0, 0, 255), 3)

        inv = 1.0 / scale  # تبدیل مختصات به اسکیل تصویر اصلی
        poly_full = [{"x": float(p[0][0] * inv), "y": float(p[0][1] * inv)} for p in approx]
        x, y, ww, hh = best_rect
        bbox_full = {"x": x * inv, "y": y * inv, "w": ww * inv, "h": hh * inv}
        rbox_full = {"cx": cx * inv, "cy": cy * inv, "w": rw * inv, "h": rh * inv, "angle": float(ang)}

        result_item = {
            "polygon": poly_full,
            "area": float(cv2.contourArea(choose) * inv * inv),
            "bbox": bbox_full,
            "rbox": rbox_full,
            "touches_edge": bool(best_edge_touch),
            # برای دیباگ (می‌تونی حذف‌شان کنی):
            # "mean_luminance": best_meanL,
            # "score": best_score,
        }

    return {
        "width": W0,
        "height": H0,
        "item": result_item,
        "overlay": overlay,   # در اسکیل رزایز‌شده
        "scale": scale,
    }

def overlay_png_bytes(overlay_bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", overlay_bgr)
    if not ok:
        raise RuntimeError("Failed to encode PNG")
    return buf.tobytes()
