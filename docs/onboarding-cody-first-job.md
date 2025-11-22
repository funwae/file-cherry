# Cody's First Job – In-App Onboarding Flow

Goal:
When a user boots FileCherry for the first time (or when there are no completed jobs yet), show a quick, **three-step overlay** called **"Cody's first job"** that explains:

1. What this box *actually* does.

2. How to run a job.

3. What to do when things break.

The tone is Cody's voice: rowdy but helpful, always giving concrete steps.

---

## Trigger Conditions

Show the onboarding if:

- There are **no job manifests** in `/data/outputs/`, and
- The user has **not dismissed** the onboarding before.

Implementation detail:

- Keep a simple "seen onboarding" flag in:
  - localStorage (for browser), and/or
  - a small JSON file in `/data/config/ui-state.json` (optional).

---

## Layout

Use a **centered modal** or full-screen overlay with 3 slides:

- Title: "Cody's first job"

- Left: Cody illustration (CodyMascot).

- Right: short copy + bullet list + "Next" / "Got it" buttons.

- Progress dots or "Step 1 of 3" at the top.

---

## Step 1 – "What this box does"

**Title:**
> "Here's the deal."

**Body copy:**

> "This isn't a website. It's a little OS on a stick.
> You dump files into `inputs/`, boot from this thing, and I drag them through AI pipelines.
> When I'm done, your cherries are stacked in `outputs/`."

**Bullet points:**

- On your *normal* computer:
  - Plug in the USB.
  - Open the drive and drag files into `inputs/`.

- On the FileCherry box (this screen):
  - I scan `inputs/`, figure out what's there, and ask what you want.
  - We run Ollama + ComfyUI + doc tools.
  - Results go into `outputs/<job-id>/`.

**Footer hint:**

> "If you remember nothing else: **inputs in, outputs out.** I'm everything in the middle."

Buttons:

- Primary: `Next`
- Secondary: `Skip intro` → sets onboarding as completed.

---

## Step 2 – "How to give Cody a job"

**Title:**
> "Tell me what you want done."

**Body copy:**

> "See that big text box on the main screen? That's where you boss me around.
> You don't have to speak 'AI'. Just say what you want done with the files you dumped."

**Example prompts (show as chips or small cards):**

- "Clean up all car photos and make them ready for listings."

- "Read all PDFs, group them by topic, and give me a summary for leadership."

- "Search across everything for anything related to 'warranty claims' and summarize."

**Explain what happens:**

> "I'll:
> - peek inside `inputs/` and see what you gave me,
> - plan a job using the local LLM (Ollama),
> - pick the right image/doc pipelines,
> - and start hauling."

**Footer hint:**

> "You can always open the **Cody chat** in the corner and say
> 'Hey Cody, what are you doing to my files right now?'"

Buttons:

- `Back`
- `Next`

---

## Step 3 – "If (when) things get weird"

**Title:**
> "When I drop a sack."

**Body copy:**

> "Sometimes jobs fail. Models crash. Disks fill up. It happens.
> When something goes sideways, here's where you look first."

**Concrete steps:**

- Check the **job status** in the UI:
  - Failed jobs will show what step blew up.

- Look at **logs**:
  - `/data/logs/orchestrator.log`
  - `/data/logs/ollama.log` (if you log it)
  - `/data/logs/comfyui.log` (optional)

- Ask **Cody chat**:
  - "Cody, why did that job fail?"
  - "Cody, is Ollama running?"
  - "Cody, where do I see the outputs?"

**Reassurance line:**

> "Worst case, nothing gets deleted. Your `inputs/` are still there.
> Fix the issue, run the job again, and I'll try not to complain."

Buttons:

- `Back`
- Primary: `Let's do my first job`
  - Closes onboarding
  - Focuses the main "what do you want to do with these files?" text box.

---

