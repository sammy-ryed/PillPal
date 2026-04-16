"""
Multi-stage image preprocessing pipeline.

Produces several processed variants of the input image so OCR engines
can try the one that works best for each prescription type.

Variant strategy
----------------
1. grayscale_clahe_adaptive  — Best for printed prescriptions
2. bilateral_sharpen         — Better for handwriting
3. grayscale_otsu            — High-contrast fallback
4. deskewed_original         — Colour image, minimal processing
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessedVariant:
    name: str
    image: np.ndarray       # BGR or grayscale numpy array for OpenCV
    pil_image: Image.Image  # PIL image for pytesseract
    description: str


class ImagePreprocessor:
    """Stateless image preprocessor. Call preprocess() with raw image bytes."""

    MAX_DIMENSION = 2400  # Resize if either side exceeds this
    MIN_TEXT_H = 900
    MIN_TEXT_W = 1200

    def preprocess(self, image_bytes: bytes) -> List[ProcessedVariant]:
        """Return a list of variants ordered by expected quality (best first)."""
        img = self._load(image_bytes)
        img = self._exif_rotate(image_bytes, img)
        img = self._crop_to_text_region(img)
        img = self._upscale_small_text(img)
        img = self._resize(img)
        img = self._deskew(img)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        variants: List[ProcessedVariant] = [
            self._variant_clahe_adaptive(gray),
            self._variant_bilateral_sharpen(gray),
            self._variant_otsu(gray),
            self._variant_colour(img),
        ]

        logger.debug(f"Produced {len(variants)} image variants.")
        return variants

    # ── Loaders ────────────────────────────────────────────────────────────────

    def _load(self, image_bytes: bytes) -> np.ndarray:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image. Unsupported format or corrupt file.")
        return img

    def _exif_rotate(self, image_bytes: bytes, img: np.ndarray) -> np.ndarray:
        """Correct rotation using EXIF orientation tag."""
        try:
            import io
            pil = Image.open(io.BytesIO(image_bytes))
            pil = ImageOps.exif_transpose(pil)
            return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception:
            return img

    def _resize(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        max_dim = max(h, w)
        if max_dim > self.MAX_DIMENSION:
            scale = self.MAX_DIMENSION / max_dim
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return img

    def _crop_to_text_region(self, img: np.ndarray) -> np.ndarray:
        """
        Remove oversized blank margins and keep only the text-rich region.

        Helpful for captures where prescription text occupies a small area of a
        large canvas (common in screenshots/camera app exports).
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            inv = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                41,
                15,
            )

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
            inv = cv2.dilate(inv, kernel, iterations=2)

            contours, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return img

            h, w = gray.shape[:2]
            min_area = max(80, int(h * w * 0.00003))
            boxes: List[Tuple[int, int, int, int]] = []

            for contour in contours:
                x, y, bw, bh = cv2.boundingRect(contour)
                area = bw * bh
                if area < min_area:
                    continue
                if bw < 10 or bh < 8:
                    continue
                boxes.append((x, y, bw, bh))

            if not boxes:
                return img

            x1 = min(x for x, _, _, _ in boxes)
            y1 = min(y for _, y, _, _ in boxes)
            x2 = max(x + bw for x, _, bw, _ in boxes)
            y2 = max(y + bh for _, y, _, bh in boxes)

            bw = x2 - x1
            bh = y2 - y1
            box_ratio = (bw * bh) / float(w * h)

            # Ignore near-full-image boxes or tiny noise-only boxes.
            if box_ratio > 0.90:
                return img
            if bw < int(w * 0.10) and bh < int(h * 0.08):
                return img

            pad = int(max(bw, bh) * 0.10) + 12
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(w, x2 + pad)
            y2 = min(h, y2 + pad)

            cropped = img[y1:y2, x1:x2]
            if cropped.size == 0:
                return img

            logger.debug(
                f"Auto-cropped text region: ({x1},{y1})-({x2},{y2}) "
                f"ratio={((x2 - x1) * (y2 - y1)) / float(w * h):.3f}"
            )
            return cropped
        except Exception as exc:
            logger.warning(f"Auto-crop failed: {exc}")
            return img

    def _upscale_small_text(self, img: np.ndarray) -> np.ndarray:
        """
        Upscale small crops so OCR engines receive larger glyphs.
        """
        h, w = img.shape[:2]
        if h >= self.MIN_TEXT_H and w >= self.MIN_TEXT_W:
            return img

        scale_h = self.MIN_TEXT_H / max(h, 1)
        scale_w = self.MIN_TEXT_W / max(w, 1)
        scale = max(scale_h, scale_w, 1.0)
        scale = min(scale, 3.0)

        if scale <= 1.05:
            return img

        new_w = int(w * scale)
        new_h = int(h * scale)
        upscaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        logger.debug(f"Upscaled text region by {scale:.2f}x to {new_w}x{new_h}.")
        return upscaled

    def _deskew(self, img: np.ndarray) -> np.ndarray:
        """Detect and correct skew angle using Hough line transform."""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=100, maxLineGap=10)

            if lines is None or len(lines) == 0:
                return img

            angles: List[float] = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 != 0:
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    if -15 < angle < 15:  # Only correct minor skew
                        angles.append(angle)

            if not angles:
                return img

            median_angle = float(np.median(angles))
            if abs(median_angle) < 0.5:
                return img

            h, w = img.shape[:2]
            M = cv2.getRotationMatrix2D((w / 2, h / 2), median_angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            logger.debug(f"Deskewed by {median_angle:.2f} degrees.")
            return rotated
        except Exception as exc:
            logger.warning(f"Deskew failed: {exc}")
            return img

    # ── Variants ───────────────────────────────────────────────────────────────

    def _variant_clahe_adaptive(self, gray: np.ndarray) -> ProcessedVariant:
        """
        CLAHE + adaptive threshold.
        Best for printed prescriptions under uneven lighting.
        """
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Unsharp mask for crispness
        blur = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        enhanced = cv2.addWeighted(enhanced, 1.5, blur, -0.5, 0)

        thresh = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=31, C=10,
        )
        return ProcessedVariant(
            name="grayscale_clahe_adaptive",
            image=thresh,
            pil_image=Image.fromarray(thresh),
            description="CLAHE + adaptive threshold (printed text)",
        )

    def _variant_bilateral_sharpen(self, gray: np.ndarray) -> ProcessedVariant:
        """
        Bilateral filter + moderate sharpen.
        Preserves edges better, handles handwriting more gracefully.
        """
        bilateral = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(bilateral, -1, kernel)

        # Otsu for clean binarisation after sharpening
        _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return ProcessedVariant(
            name="bilateral_sharpen",
            image=thresh,
            pil_image=Image.fromarray(thresh),
            description="Bilateral filter + sharpen + Otsu (handwriting)",
        )

    def _variant_otsu(self, gray: np.ndarray) -> ProcessedVariant:
        """Simple Otsu — fast, high-contrast fallback."""
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return ProcessedVariant(
            name="grayscale_otsu",
            image=thresh,
            pil_image=Image.fromarray(thresh),
            description="Otsu threshold (high-contrast fallback)",
        )

    def _variant_colour(self, img: np.ndarray) -> ProcessedVariant:
        """CLAHE on each channel, minimal processing. Good for coloured Rx pads."""
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_ch = clahe.apply(l_ch)
        enhanced = cv2.merge((l_ch, a_ch, b_ch))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        pil = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
        return ProcessedVariant(
            name="deskewed_original",
            image=enhanced,
            pil_image=pil,
            description="Colour CLAHE (minimal processing)",
        )

    def quality_score(self, gray: np.ndarray) -> float:
        """
        Estimate image quality using Laplacian variance.
        Higher = sharper = better for OCR.
        Returns a normalised score 0-1.
        """
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Sigmoid-like normalisation: score ≥ 0.85 at var ≥ 1000
        return float(min(lap_var / 1000.0, 1.0))
