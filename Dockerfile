FROM ubuntu:24.04

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# ---- 基本ツールと依存関係 ----
RUN apt-get update && apt-get install -y \
    python3.12 python3.12-venv python3.12-dev python3-pip \
    build-essential pkg-config git \
    libgl1 libglib2.0-0 tesseract-ocr \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---- 依存パッケージ (uv 使用) ----
COPY pyproject.toml uv.lock ./
RUN pip install --break-system-packages uv && uv pip install --system --break-system-packages .

# ---- アプリ資産コピー ----
COPY analyze_relics.py analyze_relics.spec ./
COPY labeled_chars ./labeled_chars

# ---- 出力ディレクトリ設定 ----
RUN mkdir -p /app/output
VOLUME ["/app/output"]

# ---- 実行コマンド ----
CMD ["python3.12", "analyze_relics.py"]
