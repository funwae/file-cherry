# LLM Orchestration with Ollama

## Role of Ollama

Ollama provides the **reasoning and planning layer** of the system.

Responsibilities:

- Interpreting user's natural language intent.
- Understanding available files (via inventory summary).
- Selecting appropriate operations/pipelines.
- Producing structured plans instead of just prose.
- Assisting with prompt-generation for downstream tools.
- Optionally generating written outputs (reports, summaries).

## Planning Protocol

### Inputs to Planner Prompt

- Appliance description (static system prompt).
- File inventory (summarized).
- Example tasks and tool schema.
- User's request.

Example high-level system prompt (conceptual):

> You are the planning brain of an offline AI appliance.
> The user has dropped files into an "inputs" folder and asked for help.
> You must respond ONLY with JSON describing which tools to invoke.

Tool schema (conceptual):

```jsonc
{
  "tools": [
    {
      "name": "IMAGE_PIPELINE",
      "params": {
        "purpose": "string",
        "style": "string?",
        "input_paths": "string[]"
      }
    },
    {
      "name": "DOC_ANALYSIS",
      "params": {
        "query": "string",
        "input_paths": "string[]",
        "output_kind": "summary|qa|clustered_report"
      }
    }
  ]
}
```

### Planner Output

Ollama returns a list of **steps**:

```json
{
  "plan": {
    "summary": "Clean up all car images; summarize all PDFs about Q1 sales.",
    "steps": [
      {
        "tool": "IMAGE_PIPELINE",
        "params": {
          "purpose": "dealership-ready car listing photos",
          "style": "bright, neutral background",
          "input_paths": ["inputs/cars/photo-001.jpg", "..."]
        }
      },
      {
        "tool": "DOC_ANALYSIS",
        "params": {
          "query": "Summarize key sales metrics and highlight problems.",
          "input_paths": ["inputs/reports/2024-q1.pdf"],
          "output_kind": "clustered_report"
        }
      }
    ]
  }
}
```

The orchestrator validates JSON and maps each step to actual services.

## Execution Interaction

* Orchestrator sends additional LLM prompts for:

  * generating detailed prompts for summarization.
  * crafting instructions for ComfyUI (e.g., textual inversion terms, style).
* For doc analysis, Ollama can:

  * read chunked text extracted by the doc-service.
  * generate final natural-language reports.

## Conversation Mode vs Batch Mode

Two modes:

1. **Batch Mode (default)**:

   * user gives a single instruction.
   * system executes all planned steps until completion.

2. **Interactive Mode (future/advanced)**:

   * user can iteratively refine plan:

     * "Make it less saturated."
     * "Also create a CSV of the key metrics."

UI can surface a "Refine" step that triggers new planning prompts using previous context.

## Agentic Extensions (Automated Agent Build-Out)

Internally we can model the orchestrator + Ollama as an **agent** with tools:

* Tools:

  * `scan_inputs`
  * `run_image_pipeline`
  * `run_doc_analysis`
  * `modify_comfy_graph`
  * `write_manifest`
* We keep the control loop in Python (for reliability), but:

  * allow Ollama to suggest tool invocations.
  * orchestrator validates and executes.

This pattern keeps:

* determinism and safety in the orchestrator
* creativity and flexibility in Ollama.

