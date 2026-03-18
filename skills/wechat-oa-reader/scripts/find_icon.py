import argparse
import os

import cv2


def find_icon(target_path: str, template_path: str, output_path: str, threshold: float = 0.8):
    print(f"Loading target image: {target_path}")
    print(f"Loading template image: {template_path}")

    img = cv2.imread(target_path)
    template = cv2.imread(template_path)

    if img is None:
        raise SystemExit(f"Error: 找不到目标图片 {target_path}")
    if template is None:
        raise SystemExit(f"Error: 找不到模板图片 {template_path}")

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    h, w = template_gray.shape

    result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        print(f"\n❌ 匹配失败。最高相似度仅为 {max_val * 100:.2f}%，未达到阈值 {threshold * 100}%。")
        raise SystemExit(1)

    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    center_x = top_left[0] + w // 2
    center_y = top_left[1] + h // 2

    print("\n=== 🎯 匹配成功 ===")
    print(f"相似度: {max_val * 100:.2f}%")
    print(f"边界框范围: X:[{top_left[0]} -> {bottom_right[0]}], Y:[{top_left[1]} -> {bottom_right[1]}]")
    print(f"目标中心点坐标: (X: {center_x}, Y: {center_y})")

    cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 4)
    cv2.circle(img, (center_x, center_y), 8, (0, 255, 0), -1)

    cv2.imwrite(output_path, img)
    print(f"\n校验图片已保存至: {output_path}")

    # Print machine-readable last line
    print(f"RESULT center_x={center_x} center_y={center_y} x1={top_left[0]} y1={top_left[1]} x2={bottom_right[0]} y2={bottom_right[1]} score={max_val:.4f}")


def default_paths():
    here = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.abspath(os.path.join(here, ".."))
    screen_dir = "/Users/dengc_mac/Projects/image_output/screenshots"
    target = os.path.join(screen_dir, "wechat_fullscreen.png")
    template = os.path.join(skill_root, "assets", "templates", "icon_template.png")
    out = os.path.join(screen_dir, "wechat_vision_check.png")
    return target, template, out


def main():
    target_default, template_default, out_default = default_paths()

    ap = argparse.ArgumentParser(description="Template match an icon in a screenshot and output an annotated image.")
    ap.add_argument("--target_path", default=target_default, help="Target image path (screenshot)")
    ap.add_argument("--template_path", default=template_default, help="Template image path")
    ap.add_argument("--output_path", default=out_default, help="Output annotated image path")
    ap.add_argument("--threshold", type=float, default=0.8, help="Match threshold (0-1)")
    args = ap.parse_args()

    find_icon(args.target_path, args.template_path, args.output_path, threshold=args.threshold)


if __name__ == "__main__":
    main()
