import cv2
import numpy as np
import os
import math
from glob import glob

# === 設定 ===
VIDEO_DIR = './videos/'
OUTPUT_DIR = './labeled_chars/'
FRAME_SKIP = 1
DIFF_SAVE_THRESHOLD_NAME = 150
DIFF_SAVE_THRESHOLD_CHAR = 40
CHAR_WIDTH_BASE = 40
CALC_BASE_WIDTH = 3840
CALC_BASE_HEIGHT = 2160

# 保存ディレクトリ作成
os.makedirs(os.path.join(OUTPUT_DIR, 'name'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'effect'), exist_ok=True)

# === 前処理（差分用） ===
def preprocess_for_diff(img_gray):
    if img_gray is None or img_gray.size == 0:
        return img_gray
    img_gray = cv2.GaussianBlur(img_gray, (3,3), 0)
    _, _ = cv2.threshold(img_gray, 170, 255, cv2.THRESH_BINARY)
    edge = cv2.Canny(img_gray, 50, 150)
    return edge

# === 保存済み画像キャッシュ ===
def load_saved_images_to_mem(directory):
    mem_list = []
    for fname in sorted(os.listdir(directory)):
        path = os.path.join(directory, fname)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            mem_list.append(preprocess_for_diff(img))
    return mem_list

saved_name_imgs = load_saved_images_to_mem(os.path.join(OUTPUT_DIR, 'name'))
saved_effect_imgs = load_saved_images_to_mem(os.path.join(OUTPUT_DIR, 'effect'))
print(f"既存キャッシュ: name={len(saved_name_imgs)}, effect={len(saved_effect_imgs)}")

# === 差分判定 ===
def is_new_image_mem(img_proc, saved_images_mem, diff_save_threshold):
    for saved_proc in saved_images_mem:
        if saved_proc.shape != img_proc.shape:
            saved_resized = cv2.resize(saved_proc, (img_proc.shape[1], img_proc.shape[0]), interpolation=cv2.INTER_AREA)
        else:
            saved_resized = saved_proc
        diff = cv2.countNonZero(cv2.absdiff(img_proc, saved_resized))
        if diff < diff_save_threshold:
            return False
    return True

# === ROI座標 ===
def scaled_rect(x1, y1, x2, y2, frame_w, frame_h):
    sx = math.floor(frame_w  * x1 / CALC_BASE_WIDTH)
    sy = math.floor(frame_h * y1 / CALC_BASE_HEIGHT)
    ex = math.ceil(frame_w  * x2 / CALC_BASE_WIDTH)
    ey = math.ceil(frame_h * y2 / CALC_BASE_HEIGHT)
    return {"x1": sx, "y1": sy, "x2": ex, "y2": ey}

# === 動画1本処理 ===
def process_video(video_path):
    global saved_name_imgs, saved_effect_imgs

    cap = cv2.VideoCapture(video_path)
    FRAME_WIDTH  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    FRAME_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    FRAME_COUNT  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"\n▶ 処理開始: {video_path} ({FRAME_WIDTH}x{FRAME_HEIGHT}, {FRAME_COUNT} frames)")

    # ROI設定
    ROIS = {
        "name": scaled_rect(2150,1550,2900,1600, FRAME_WIDTH, FRAME_HEIGHT),
        "effect1_1": scaled_rect(2220,1630,3820,1670, FRAME_WIDTH, FRAME_HEIGHT),
        "effect1_2": scaled_rect(2220,1678,3820,1720, FRAME_WIDTH, FRAME_HEIGHT),
        "effect2_1": scaled_rect(2220,1750,3820,1790, FRAME_WIDTH, FRAME_HEIGHT),
        "effect2_2": scaled_rect(2220,1798,3820,1840, FRAME_WIDTH, FRAME_HEIGHT),
        "effect3_1": scaled_rect(2220,1870,3820,1910, FRAME_WIDTH, FRAME_HEIGHT),
        "effect3_2": scaled_rect(2220,1918,3820,1960, FRAME_WIDTH, FRAME_HEIGHT),
    }

    prev_name_gray = None
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- 遺物名 ---
        roi = ROIS["name"]
        name_img = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]
        name_gray_proc = preprocess_for_diff(cv2.cvtColor(name_img, cv2.COLOR_BGR2GRAY))
        name_changed = prev_name_gray is None or cv2.countNonZero(cv2.absdiff(prev_name_gray, name_gray_proc)) > DIFF_SAVE_THRESHOLD_NAME
        if name_changed:
            if is_new_image_mem(name_gray_proc, saved_name_imgs, DIFF_SAVE_THRESHOLD_NAME):
                fname = os.path.join(OUTPUT_DIR, 'name', f"{os.path.basename(video_path)}_{frame_index}_name.png")
                cv2.imwrite(fname, cv2.cvtColor(name_img, cv2.COLOR_BGR2GRAY))
                saved_name_imgs.append(name_gray_proc)
                print(f"[{os.path.basename(video_path)}] Frame {frame_index}: name saved")
            prev_name_gray = name_gray_proc

        # --- 遺物効果（文字単位） ---
        for eff_idx in range(1,4):
            for line in [1,2]:
                key = f"effect{eff_idx}_{line}"
                roi = ROIS[key]
                eff_img = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]
                if eff_img.shape[1] <= 0 or eff_img.shape[0] <= 0:
                    continue
                char_width = int(CHAR_WIDTH_BASE * FRAME_WIDTH / CALC_BASE_WIDTH)
                n_chars = math.ceil(eff_img.shape[1] / char_width)
                for c in range(n_chars):
                    x1 = c*char_width
                    x2 = min((c+1)*char_width, eff_img.shape[1])
                    char_img = eff_img[:, x1:x2]
                    if char_img.shape[1] <= 0:
                        continue
                    char_gray_proc = preprocess_for_diff(cv2.cvtColor(char_img, cv2.COLOR_BGR2GRAY))
                    if is_new_image_mem(char_gray_proc, saved_effect_imgs, DIFF_SAVE_THRESHOLD_CHAR):
                        fname = os.path.join(OUTPUT_DIR, 'effect', f"{os.path.basename(video_path)}_{frame_index}_{key}_c{c}.png")
                        cv2.imwrite(fname, cv2.cvtColor(char_img, cv2.COLOR_BGR2GRAY))
                        saved_effect_imgs.append(char_gray_proc)
                        print(f"[{os.path.basename(video_path)}] Frame {frame_index}: {key} char {c} saved")

        # --- フレーム進める ---
        frame_index += FRAME_SKIP
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        print(f"処理中: {frame_index}/{FRAME_COUNT} ({frame_index/FRAME_COUNT*100:.1f}%)", end='\r')

    cap.release()
    print(f"\n✅ 完了: {os.path.basename(video_path)}")

# === メイン ===
video_files = sorted(glob(os.path.join(VIDEO_DIR, '*.mp4')))
print(f"検出された動画: {len(video_files)} 件")

for vpath in video_files:
    process_video(vpath)

print("\n🎉 全動画の文字単位ラベル生成完了")
