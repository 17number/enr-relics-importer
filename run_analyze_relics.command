#!/bin/bash
echo "=== ELDEN RING NIGHTREIGN Relics Analyzer ==="
cd "$(dirname "$0")" || exit 1
docker build -t enr-relics-importer .

docker run --rm \
  -v "$(pwd)/labeled_chars:/app/labeled_chars" \
  -v "$(pwd)/relics.mp4:/app/relics.mp4" \
  -v "$(pwd)/output:/app/output" \
  enr-relics-importer
