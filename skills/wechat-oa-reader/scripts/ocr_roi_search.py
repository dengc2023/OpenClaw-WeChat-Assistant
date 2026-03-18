#!/usr/bin/env python3
import sys
import easyocr
import argparse
import cv2
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Find text below an anchor text (ROI search).")
    parser.add_argument("--image_path", required=True, help="Path to the screenshot")
    parser.add_argument("--anchor_text", required=True, help="Text to use as anchor (e.g., 'Official Accounts')")
    parser.add_argument("--target_text", required=True, help="Text to click below the anchor")
    parser.add_argument("--output_path", required=True, help="Path to save the annotated image")
    parser.add_argument("--gpu", action="store_true", help="Use GPU if available")
    args = parser.parse_args()

    # Initialize reader
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=args.gpu)

    # 1. Read full image
    img = cv2.imread(args.image_path)
    if img is None:
        print(f"Error: Could not read image at {args.image_path}")
        sys.exit(1)
    
    height, width, _ = img.shape

    # 2. Find anchor text first
    print(f"Searching for anchor: '{args.anchor_text}'...")
    anchor_results = reader.readtext(args.image_path)
    
    anchor_bbox = None
    anchor_conf = 0.0

    for (bbox, text, prob) in anchor_results:
        # Case-insensitive match or substring match
        if args.anchor_text.lower() in text.lower():
            if prob > anchor_conf:
                anchor_conf = prob
                anchor_bbox = bbox # [[tl, tr, br, bl]]

    if not anchor_bbox:
        print(f"Error: Anchor text '{args.anchor_text}' not found.")
        sys.exit(1)

    print(f"Found anchor '{args.anchor_text}' at {anchor_bbox} (conf: {anchor_conf:.4f})")

    # Get bottom Y of anchor to define ROI start
    # bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] -> bottom-left y is y3 or y4
    y_start = int(max(anchor_bbox[2][1], anchor_bbox[3][1]))
    
    # 3. Crop ROI (from y_start to bottom)
    roi_img = img[y_start:height, 0:width]
    
    # Check if ROI is valid
    if roi_img.shape[0] <= 0 or roi_img.shape[1] <= 0:
        print("Error: ROI is empty.")
        sys.exit(1)

    # 4. Search target text in ROI
    print(f"Searching for target: '{args.target_text}' in ROI (y >= {y_start})...")
    # Pass numpy array directly to readtext
    target_results = reader.readtext(roi_img)
    
    target_bbox = None
    target_conf = 0.0
    matched_text = ""

    # Find best match in ROI
    for (bbox, text, prob) in target_results:
        if args.target_text.lower() in text.lower():
             # We want the FIRST match from top to bottom usually, 
             # but let's stick to highest confidence or first valid one.
             # Actually for list items, the first one is usually the one right below the header.
             # Let's just take the first match that exceeds a threshold.
             if prob > 0.5: 
                target_bbox = bbox
                target_conf = prob
                matched_text = text
                break 

    if not target_bbox:
        print(f"Error: Target text '{args.target_text}' not found in ROI.")
        sys.exit(1)

    # 5. Coordinate Translation (ROI -> Full Image)
    # ROI (x, y) -> Full (x, y + y_start)
    
    # Calculate center in ROI
    # bbox in easyocr is relative to the input image (ROI)
    # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    
    roi_x_center = int((target_bbox[0][0] + target_bbox[2][0]) / 2)
    roi_y_center = int((target_bbox[0][1] + target_bbox[2][1]) / 2)
    
    final_x = roi_x_center
    final_y = roi_y_center + y_start
    
    print(f"--- ROI MATCH ---")
    print(f"Anchor Y-bottom: {y_start}")
    print(f"Target in ROI: '{matched_text}' at ({roi_x_center}, {roi_y_center})")
    print(f"Final Global Coordinates: ({final_x}, {final_y})")
    
    # 6. Draw visualization on FULL image
    # Draw anchor box (Blue)
    cv2.rectangle(img, 
                  (int(anchor_bbox[0][0]), int(anchor_bbox[0][1])), 
                  (int(anchor_bbox[2][0]), int(anchor_bbox[2][1])), 
                  (255, 0, 0), 2)
    
    # Draw target box (Red) - need to shift y coordinates
    tl = (int(target_bbox[0][0]), int(target_bbox[0][1]) + y_start)
    br = (int(target_bbox[2][0]), int(target_bbox[2][1]) + y_start)
    
    cv2.rectangle(img, tl, br, (0, 0, 255), 2)
    
    # Draw click point (Green)
    cv2.circle(img, (final_x, final_y), 5, (0, 255, 0), -1)
    
    # Save output
    cv2.imwrite(args.output_path, img)
    print(f"Saved annotation to {args.output_path}")

if __name__ == "__main__":
    main()
