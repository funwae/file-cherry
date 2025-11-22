# ComfyUI Integration

## Purpose

Use ComfyUI as the **image-processing engine**:

- Leverage composable graph system for:
  - generation
  - enhancement
  - background removal
  - upscaling
  - style application
- Allow orchestrator (via Ollama) to adjust graph parameters for each job.

## Deployment

- ComfyUI runs as a headless server at boot:
  - `python main.py --listen 0.0.0.0 --port 8188`
- Pipelines (workflows) stored under:
  - `/data/config/comfy/pipelines/`

## Pipeline Types

Initial recommended pipelines:

1. **Photo Cleanup Pipeline**
   - Input: one or more photos.
   - Operations: background cleanup, contrast, slight sharpening, watermark removal (if allowed), resizing.
   - Output: JPEGs suitable for listings.

2. **Creative Variation Pipeline**
   - Input: base product/car photo.
   - Operations: background replacement (studio, outdoor), color variants.
   - Output: multiple variations per input.

3. **Simple Text-to-Image Pipeline**
   - Input: text prompts.
   - Output: generated images.

Each pipeline is defined as a ComfyUI graph JSON file with named input nodes.

## Orchestrator ↔ ComfyUI Contract

For each pipeline, define a **schema**:

```yaml
name: "photo_cleanup_v1"
graph_file: "car_cleanup.json"
inputs:
  - name: "IMAGE"
    type: "image_path"
params:
  - name: "brightness_adjust"
    type: "float"
    default: 1.0
  - name: "crop_ratio"
    type: "float"
    default: 1.0
outputs:
  - name: "OUTPUT_IMAGE"
    type: "image"
```

Orchestrator steps:

1. Load pipeline schema.
2. Map input paths to proper ComfyUI API payload:

   * upload images if needed.
   * set node parameters.
3. Execute graph via ComfyUI API.
4. Download resulting images into `outputs/<job-id>/images/`.

## LLM-Aware Param Tuning

Ollama can:

* read user intent ("make the cars look more premium, less saturated").
* map this to param adjustments:

  * reduce saturation
  * slightly increase contrast
  * choose appropriate styles.

We expose a mapping:

```yaml
semantic_controls:
  "premium": { "contrast": 1.1, "sharpness": 1.05 }
  "less_saturated": { "saturation": 0.9 }
```

Ollama includes these knobs in planning; orchestrator clamps values to safe ranges.

## Performance Considerations

* Batch processing:

  * group images with identical settings.
* Caching:

  * avoid re-uploading identical files.
* VRAM:

  * enforce max batch sizes based on GPU detection.

## Failure Modes

* If ComfyUI is unreachable:

  * orchestrator marks all image steps as `failed` with clear message.
* If individual images fail:

  * skip them but process others.
* Timeouts:

  * configurable per pipeline in YAML.

