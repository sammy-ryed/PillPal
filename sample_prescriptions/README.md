# Sample Prescriptions

Place prescription images here to test the OCR pipeline.

## Recommended test images

- `printed_simple.jpg` — A computer-printed prescription (easiest for OCR)
- `printed_complex.jpg` — Printed with table layout
- `handwritten_clear.jpg` — Clear handwritten prescription
- `handwritten_doctor.jpg` — Typical doctor handwriting (hardest case)
- `phone_photo.jpg` — Phone photo of prescription (real-world condition)

## Tips for good test images

- Good lighting, no shadows across text
- Flat surface — no curved paper
- Full prescription in frame — doctor name + medicine list visible
- Minimum 1MP resolution (1280x960 or better)
- JPEG, PNG, WEBP, BMP, or TIFF formats accepted

## Where to get sample prescriptions

You can use publicly available medical dataset images, or photograph any
prescription you have (with patient data redacted if sharing).

Some open datasets:
- [SROIE dataset](https://rrc.cvc.uab.es/?ch=13) — receipts, similar structure
- Create your own by typing a sample in Word and printing

## Testing the pipeline directly

```bash
curl -X POST http://localhost:8000/api/prescriptions/parse \
  -F "file=@sample_prescriptions/printed_simple.jpg"
```
