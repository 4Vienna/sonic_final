"""
fix_map.py

Compare `green_hill_1.png` to the tileset `green_hill_1_tiles.png` and produce
an updated CSV `green_hill_1_map_fixed.csv` matching tileset indices.

Usage (from project root, with your venv activated):

& .\.venv\Scripts\Activate.ps1
python tools\fix_map.py

This script uses Pillow. Install with:
& .\.venv\Scripts\Activate.ps1
pip install Pillow

"""
from PIL import Image
import os
import csv

BASE = os.path.join('resources', 'zones', 'green_hill_1')
FULL = os.path.join(BASE, 'green_hill_1.png')
TILESET = os.path.join(BASE, 'green_hill_1_tiles.png')
MAP_CSV = os.path.join(BASE, 'green_hill_1_map.csv')
OUT_CSV = os.path.join(BASE, 'green_hill_1_map_fixed.csv')

TILE = 16


def slice_tileset(tileset_path, tile_size):
    img = Image.open(tileset_path).convert('RGBA')
    w, h = img.size
    cols = w // tile_size
    rows = h // tile_size
    tiles = []
    for r in range(rows):
        for c in range(cols):
            box = (c*tile_size, r*tile_size, c*tile_size+tile_size, r*tile_size+tile_size)
            t = img.crop(box)
            tiles.append(t)
    return tiles


def img_to_bytes(im):
    return im.tobytes()


def mse_bytes(a: bytes, b: bytes) -> float:
    # Mean squared error between two equal-length byte sequences
    s = 0
    # use memoryview for speed
    mv1 = memoryview(a)
    mv2 = memoryview(b)
    for i in range(len(mv1)):
        d = mv1[i] - mv2[i]
        s += d*d
    return s / len(mv1)


def main():
    print('Loading images...')
    full = Image.open(FULL).convert('RGBA')
    tiles = slice_tileset(TILESET, TILE)
    tile_bytes = [img_to_bytes(t) for t in tiles]

    # read csv to get grid size
    with open(MAP_CSV, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = [r for r in reader]

    h = len(rows)
    w = len(rows[0]) if h>0 else 0
    print('Map grid:', w, 'x', h)

    out_rows = []
    total = 0
    exact = 0
    approx = 0

    for ry in range(h):
        out_row = []
        for rx in range(w):
            total += 1
            x = rx * TILE
            y = ry * TILE
            if x+TILE > full.width or y+TILE > full.height:
                out_row.append('-1')
                continue
            patch = full.crop((x,y,x+TILE,y+TILE))
            pb = img_to_bytes(patch)
            # try exact
            found = False
            for idx, tb in enumerate(tile_bytes):
                if tb == pb:
                    out_row.append(str(idx))
                    exact += 1
                    found = True
                    break
            if found:
                continue
            # approximate: find tile with minimum mse
            best_idx = None
            best_mse = None
            for idx, tb in enumerate(tile_bytes):
                m = mse_bytes(pb, tb)
                if best_mse is None or m < best_mse:
                    best_mse = m
                    best_idx = idx
            out_row.append(str(best_idx if best_idx is not None else -1))
            approx += 1
        out_rows.append(out_row)

    # write out csv
    with open(OUT_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(out_rows)

    print('Total tiles:', total)
    print('Exact matches:', exact)
    print('Approx (fallback) matches:', approx)
    print('Wrote:', OUT_CSV)

if __name__ == '__main__':
    main()
