# media-processor
Processes Video and Images to resize, rename using SEO, and make it much easier to edit photos and label them for projects like websites, webapps, and Android and iOS apps. 

## Image processor GUI

This repository includes a Python GUI (`app.py`) that lets you:
- choose photos from your file explorer/finder
- pick a usage target (Facebook, Instagram, X, Website, Google Business)
- pick a crop ratio for that target
- convert to web-ready image formats (`webp`, `jpg`, `png`)

Processed files are saved to:
- `storage/photos/social-accounts/{social-media-name}` for social targets
- `storage/website/photos` for Website

### Run

```bash
python -m pip install -r requirements.txt
python app.py
```
