import numpy as np
from PIL import Image, ImageDraw

from preprocess import adaptive_threshold, grayscale, deskew, binarize, resize


def test_grayscale_converts_to_l_mode():
    img = Image.new("RGB", (10, 10), "red")
    gray = grayscale(img)
    assert gray.mode == "L"


def test_binarize_produces_binary_image():
    arr = np.tile(np.linspace(0, 255, 10, dtype=np.uint8), (10, 1))
    img = Image.fromarray(arr)
    binary = binarize(img)
    uniq = np.unique(np.array(binary))
    assert set(uniq).issubset({0, 255})


def test_adaptive_threshold_produces_binary_image():
    arr = np.tile(np.linspace(0, 255, 10, dtype=np.uint8), (10, 1))
    img = Image.fromarray(arr)
    binary = adaptive_threshold(img)
    uniq = np.unique(np.array(binary))
    assert set(uniq).issubset({0, 255})


def test_binarize_adaptive_method():
    arr = np.tile(np.linspace(0, 255, 10, dtype=np.uint8), (10, 1))
    img = Image.fromarray(arr)
    binary = binarize(img, method="adaptive")
    uniq = np.unique(np.array(binary))
    assert set(uniq).issubset({0, 255})


def test_resize_limits_max_dimension():
    img = Image.new("RGB", (200, 100), "white")
    resized = resize(img, 100)
    assert max(resized.size) == 100


def test_deskew_rotated_image():
    img = Image.new("L", (100, 100), 255)
    draw = ImageDraw.Draw(img)
    draw.rectangle((10, 40, 90, 60), fill=0)
    rotated = img.rotate(15, expand=True, fillcolor=255)
    result = deskew(rotated)
    gray = np.array(result.convert("L"))
    coords = np.column_stack(np.where(gray < 255))
    if coords.size:
        y = coords[:, 0]
        x = coords[:, 1]
        cov = np.cov(x, y)
        eigvals, eigvecs = np.linalg.eig(cov)
        principal = eigvecs[:, np.argmax(eigvals)]
        angle = np.degrees(np.arctan2(principal[1], principal[0]))
    else:
        angle = 0
    assert abs(angle) < 1
