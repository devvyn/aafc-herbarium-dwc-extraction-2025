# OCR Engine Preprocessing Flows

This document summarizes recommended preprocessing steps for each supported OCR engine. The steps correspond to functions in `preprocess` and can be composed via the `pipeline` list in the configuration file's `[preprocess]` section.

## Apple Vision

| Step     | Purpose                                   | Recommended range |
|----------|-------------------------------------------|-------------------|
| `resize` | Limit longest edge for memory efficiency   | `max_dim_px` 2500–3500 (default 3072) |

Apple's Vision framework handles color balance and skew internally, so additional preprocessing is rarely required.

## Tesseract

| Step        | Purpose                                         | Recommended range |
|-------------|-------------------------------------------------|-------------------|
| `grayscale` | Remove color information                        | — |
| `contrast`  | Enhance text/background separation              | `contrast_factor` 1.3–1.7 |
| `deskew`    | Correct rotation based on principal components  | — |
| `binarize`  | Otsu threshold to isolate foreground            | — |
| `resize`    | Improve OCR accuracy at higher resolution       | `max_dim_px` 3000–4000 |

This sequence yields high-quality input for Tesseract by maximizing contrast and text sharpness before recognition.

## GPT (ChatGPT)

| Step        | Purpose                                   | Recommended range |
|-------------|-------------------------------------------|-------------------|
| `grayscale` | Simplify image while retaining detail      | — |
| `contrast`  | Light enhancement to aid tokenization     | `contrast_factor` 1.2–1.5 |
| `resize`    | Control token count in prompts            | `max_dim_px` 1500–2500 (default 2048) |

GPT-based OCR operates on lower resolutions; moderate preprocessing keeps images concise while remaining legible.

---

Example prototype configurations are available in `preprocess/flows.py` for quick experimentation.
