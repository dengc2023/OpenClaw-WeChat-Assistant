import argparse
from pathlib import Path

import cv2
import numpy as np
import easyocr


def main():
    ap = argparse.ArgumentParser(description="OCR locate a text query in a screenshot and output an annotated image.")
    ap.add_argument("--image_path", required=True, help="Input screenshot path")
    ap.add_argument("--query_text", required=True, help="Text to search for in the image")
    ap.add_argument("--output_path", default=None, help="Output annotated image path (default: <image_stem>_ocr_box.png)")
    args = ap.parse_args()

    image_path = Path(args.image_path).expanduser()
    query = args.query_text
    out_path = Path(args.output_path).expanduser() if args.output_path else image_path.with_name(image_path.stem + "_ocr_box.png")

    img = cv2.imread(str(image_path))
    if img is None:
        raise SystemExit(f"Cannot read image: {image_path}")

    # EasyOCR expects RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    results = reader.readtext(img_rgb)

    # Find best match by substring overlap
    best = None
    best_score = -1
    for (bbox, text, conf) in results:
        if not text:
            continue
        # simple scoring: how many query chars appear in text
        score = sum(1 for ch in query if ch in text)
        if score > best_score:
            best_score = score
            best = (bbox, text, conf)

    if best is None:
        raise SystemExit("No OCR text found")

    bbox, text, conf = best
    # bbox: 4 points [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    pts = np.array(bbox, dtype=np.int32)

    x_min = int(np.min(pts[:, 0])); x_max = int(np.max(pts[:, 0]))
    y_min = int(np.min(pts[:, 1])); y_max = int(np.max(pts[:, 1]))

    cx = int((x_min + x_max) / 2)
    cy = int((y_min + y_max) / 2)

    # Draw red rectangle and green center point
    cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 0, 255), 4)
    cv2.circle(img, (cx, cy), 8, (0, 255, 0), -1)

    cv2.imwrite(str(out_path), img)

    print("--- OCR MATCH ---")
    print(f"query: {query}")
    print(f"matched_text: {text}")
    print(f"confidence: {conf:.4f}")
    print(f"bbox: x[{x_min},{x_max}] y[{y_min},{y_max}]")
    print(f"center: ({cx},{cy})")
    print(f"output: {out_path}")


if __name__ == '__main__':
    main()
