# OCR engine preprocessing flows

This document summarizes recommended preprocessing steps for each supported OCR engine. The steps correspond to functions in `preprocess` and can be composed via the `pipeline` list in the configuration file's `[preprocess]` section.

## Multilingual setup

List the languages your project needs under `[ocr].langs` in the configuration. Tesseract models can be mapped explicitly via `[tesseract].model_paths`, allowing custom `.traineddata` locations. When no languages are provided, engines attempt automatic detection.
PaddleOCR uses a single language code configured under `[paddleocr].lang`.

Future work will integrate dedicated multilingual OCR models for non-English labels ([Issue #138](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/138)).

## Apple Vision

| Step     | Purpose                                   | Recommended range |
|----------|-------------------------------------------|-------------------|
| `resize` | Limit longest edge for memory efficiency   | `max_dim_px` 2500–3500 (default 3072) |

Apple's Vision framework handles color balance and skew internally, so additional preprocessing is rarely required.

## Tesseract

| Step        | Purpose                                         | Recommended range |
|-------------|-------------------------------------------------|-------------------|
| `grayscale` | Remove color information                        | — |
| `contrast`  | Enhance text/background separation              | `contrast_factor` 1.3–1.7 (default 1.5) |
| `deskew`    | Correct rotation based on principal components  | — |
| `binarize`  | Otsu or adaptive (Sauvola) threshold            | `binarize_method` "otsu" or "adaptive" |
| `resize`    | Improve OCR accuracy at higher resolution       | `max_dim_px` 3000–4000 |

This sequence yields high-quality input for Tesseract by maximizing contrast and text sharpness before recognition.

## PaddleOCR

| Step        | Purpose                                 | Recommended range |
|-------------|-----------------------------------------|-------------------|
| `grayscale` | Remove color information                | — |
| `binarize`  | Adaptive thresholding for clearer text  | `binarize_method` "adaptive" |
| `resize`    | Improve recognition at higher resolution | `max_dim_px` 3000–4000 |

PaddleOCR handles mild skew but benefits from binarized input.

## GPT (ChatGPT)

| Step        | Purpose                                   | Recommended range |
|-------------|-------------------------------------------|-------------------|
| `grayscale` | Simplify image while retaining detail      | — |
| `contrast`  | Light enhancement to aid tokenization     | `contrast_factor` 1.2–1.5 (default 1.3) |
| `resize`    | Control token count in prompts            | `max_dim_px` 1500–2500 (default 2048) |

GPT-based OCR operates on lower resolutions; moderate preprocessing keeps images concise while remaining legible.

---

Example prototype configurations are available in `preprocess/flows.py` for quick experimentation.
