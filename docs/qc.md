# Quality control review

During the QC phase, confirm OCR candidates alongside the source image.

```bash
python review.py --tui path/to/candidates.db specimen.jpg
```

Use the arrow keys to highlight a candidate and press Enter to confirm. The chosen value is persisted through [`io_utils.candidates.record_decision`](../io_utils/candidates.py). If the terminal cannot display images, a text placeholder is shown instead.
