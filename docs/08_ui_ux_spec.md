# UI / UX Specification

## Design Goals

- Minimal.
- Non-threatening.
- Clear "Files in / Files out" metaphor.

## Entry Screen

On boot (after services up), show:

- Logo + name.
- Quick status summary:
  - number of files detected in `inputs/` by type.
  - a note if `inputs/` is empty.

Example:

> **FileCherry Appliance**
> Found 32 files in `inputs/`
> - 24 images
> - 8 documents
>
> _What do you want to do with these files?_

### Input Area

- Single large text box (multi-line) with placeholder:
  > "Describe in your own words what you want done. Example:
  > 'Make dealership-ready photos from the images and produce a summary of all the PDFs.'"

- "Continue" button.

## Plan Review Screen

After plan creation:

- Show a human-readable version of the LLM-generated plan:

> **Proposed plan**
> 1. Enhance and clean up 24 car photos for online listings.
> 2. Summarize 8 PDFs into a 2-page report highlighting key sales metrics.
>
> [Edit] [Looks good → Run]

- "Edit" opens a simple text field to refine the request; triggers re-planning.

## Job Progress Screen

Show:

- Job ID.
- Step-by-step progress:

```text
[✓] Step 1: Scan and classify inputs
[●] Step 2: Process 24 images (6/24 complete)
[○] Step 3: Analyze 8 documents
```

* One-line status updates ("Running ComfyUI pipeline 'photo_cleanup_v1'…").
* Estimation (rough) when possible.

Buttons:

* "Cancel job" (with confirmation).
* "View logs" (advanced toggle).

## Completion Screen

* Big "Job complete" message.
* Summary:

  * "24 images processed, 8 docs analyzed."
* Output location:

  * "Results saved in `outputs/20251121-154230-8f3a`."
* Option:

  * "View file tree" (shows a simple browser of outputs).

Instructions:

> "You can now shut down, plug the USB into your usual computer, and open `outputs/20251121-154230-8f3a`."

## Error UX

* When something fails:

  * simple explanation:

    > "ComfyUI could not process 3 images. The other 21 were completed."
  * suggestion:

    > "Try removing extremely large images or corrupted files from `inputs/` and run again."

* Provide a short error code that maps to a log entry.

## Advanced UI (Optional / Toggle in config)

If `config/appliance.yaml` sets `show_advanced: true`:

* Add an "Advanced" button that reveals:

  * model selection
  * pipeline options
  * dry-run mode (planning only)
  * access to config validation.

Default for end users: disabled.

