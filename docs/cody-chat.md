# Cody Chat – In-OS Assistant for FileCherry

## 1. UX Decision: Integrated but Not Confusing

We'll treat **Chat with Cody** as:

- a **persistent chat drawer** in the main appliance UI

- that can:

  1. **answer questions / explain errors / guide usage**, and

  2. **announce and narrate jobs** that are created from the main "What do you want to do with these files?" flow.

For v1:

- **Job creation stays in the main "Action" panel.**

  (The big prompt that turns your request into a plan and runs a job.)

- **Cody chat is integrated at the UI level**, not the orchestration level:

  - The Action panel can *optionally* **ghost-post** your task description into the chat ("User: Here's what I just told you to do"), and Cody replies with a natural-language confirmation.

  - Cody chat itself does **not** spawn jobs yet. It just talks about them.

This keeps things simple:

- Users always know:

  > "I start jobs over here, I talk to Cody over there."

- But the experience still feels unified because Cody *narrates* the job.

Later (Phase N) we can add a toggle:

> "Let Cody turn this message into a new job",

but we **don't** do that now.

---

## 2. High-Level Architecture

**Components:**

1. **Cody System Prompt File**

   - `config/llm/cody_system_prompt.md` – text prompt defining Cody's persona & style.

2. **Backend Cody Chat Endpoint (FastAPI / orchestrator)**

   - `POST /api/cody/chat`

   - Uses Ollama chat API with `system` prompt from the file above.

3. **Frontend Cody Chat Panel**

   - `apps/ui/src/components/CodyChatPanel.tsx`

   - Slide-up or side drawer chat UI with Cody avatar.

4. **UI Shell Wiring**

   - Add a "Chat with Cody" button/icon in the main app layout.

   - The existing "Action" panel can push messages into the Cody chat stream.

---

## 3. System Prompt for Cody (pulled from copy & voice guide)

Create file:

`config/llm/cody_system_prompt.md`

```md

You are **Cody the Cherry Picker**, the mascot and voice of FileCherry.

FileCherry is a bootable, offline-first AI appliance on a USB stick. Users:

- copy files into an `inputs/` folder on the stick,

- boot from it,

- tell FileCherry what they want,

- and pick up results in `outputs/`.

Your personality:

- Blue-collar competent: you know your tools (Ollama, ComfyUI, the orchestrator, Linux basics).

- Rowdy & impatient in a friendly way: you want the user to give you work, not theory.

- You roast the **chaos of their files**, never the person.

Tone:

- Plainspoken, clear, concrete.

- Light sarcasm is allowed, but always followed by a helpful, practical answer.

- Avoid corporate buzzwords and mystical AI language.

- Use short sentences and give paths or commands where useful.

When answering:

- Prioritize **FileCherry usage**:

  - how to structure `inputs/` and `outputs/`,

  - how jobs run,

  - how to read manifests and logs,

  - basic troubleshooting (services, ports, common errors).

- If asked about internal architecture, you can describe:

  - Ubuntu-based live OS,

  - Python orchestrator calling Ollama and ComfyUI,

  - document processing (extract → index → summarize).

- If you don't know something, say so plainly and suggest where in the docs the user might look (for example: "check the docs folder under 'testing-strategy'" or similar).

Examples of your voice:

- "Drop your mess into `inputs/`, I'll deal with it."

- "Outputs are in `outputs/<job-id>/`. Don't make me say it twice."

- "Yes, I'll process the file named `final_v7_REAL_final_USE_THIS_ONE.pdf`. Again."

Never claim to send data to remote servers by default. FileCherry is local-first.

If a feature would require the internet, clearly mark it as optional and opt-in.

```

Backend will read this file at startup (or cache it on first use) and pass as `system` prompt to Ollama.

---

## 4. Backend Implementation (Orchestrator)

### 4.1 Data Types

Add a simple model in `src/orchestrator/models/cody_chat.py`:

```py

from pydantic import BaseModel

from typing import Literal, List

Role = Literal["system", "user", "assistant"]

class CodyMessage(BaseModel):

    role: Role

    content: str

class CodyChatRequest(BaseModel):

    messages: List[CodyMessage]

class CodyChatResponse(BaseModel):

    reply: str

```

### 4.2 Ollama Client Helper

If you already have an Ollama client module, extend it.

Otherwise, create `src/orchestrator/llm/ollama_client.py` with a generic `chat` function, then add a wrapper for Cody:

```py

import os

import httpx

from typing import List, Dict

from .schemas import CodyMessage  # adjust import path

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

CODY_MODEL = os.getenv("CODY_MODEL", "phi3:mini")

def load_cody_system_prompt() -> str:

    path = os.getenv(

        "CODY_SYSTEM_PROMPT_PATH",

        "/opt/filecherry/config/llm/cody_system_prompt.md",

    )

    with open(path, "r", encoding="utf-8") as f:

        return f.read()

_cody_system_prompt = None

def get_cody_system_prompt() -> str:

    global _cody_system_prompt

    if _cody_system_prompt is None:

        _cody_system_prompt = load_cody_system_prompt()

    return _cody_system_prompt

async def cody_chat(messages: List[CodyMessage]) -> str:

    """

    Call Ollama chat with Cody's persona and return the assistant reply text.

    """

    system_prompt = get_cody_system_prompt()

    ollama_messages: List[Dict[str, str]] = [

        {"role": "system", "content": system_prompt}

    ]

    for m in messages:

        if m.role == "system":

            # Ignore extra system messages from client; Cody persona is fixed.

            continue

        ollama_messages.append({"role": m.role, "content": m.content})

    payload = {

        "model": CODY_MODEL,

        "messages": ollama_messages,

        "stream": False,

    }

    async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=60) as client:

        resp = await client.post("/v1/chat/completions", json=payload)

        resp.raise_for_status()

        data = resp.json()

    # shape depends on how you proxy to Ollama; adjust as needed

    # Example OpenAI-compatible proxy:

    reply = data["choices"][0]["message"]["content"]

    return reply

```

(If you're talking directly to Ollama's native API, swap `/v1/chat/completions` & payload accordingly.)

### 4.3 FastAPI Route

In your API router (e.g. `src/orchestrator/api/routes_cody.py`):

```py

from fastapi import APIRouter

from .models.cody_chat import CodyChatRequest, CodyChatResponse

from ..llm.ollama_client import cody_chat

router = APIRouter(prefix="/cody", tags=["cody"])

@router.post("/chat", response_model=CodyChatResponse)

async def chat_with_cody(req: CodyChatRequest) -> CodyChatResponse:

    reply = await cody_chat(req.messages)

    return CodyChatResponse(reply=reply)

```

Then include this router in your main API (`/api/cody/chat`).

---

## 5. Frontend – Cody Chat Panel

### 5.1 Component

Create file: `apps/ui/src/components/CodyChatPanel.tsx`

```tsx

"use client";

import { useState } from "react";

import { CodyMascot } from "./CodyMascot";

type Role = "user" | "assistant";

interface ChatMessage {

  role: Role;

  content: string;

}

interface CodyChatPanelProps {

  defaultOpen?: boolean;

}

export function CodyChatPanel({ defaultOpen = false }: CodyChatPanelProps) {

  const [open, setOpen] = useState(defaultOpen);

  const [messages, setMessages] = useState<ChatMessage[]>([

    {

      role: "assistant",

      content:

        "I'm Cody. You dump files in `inputs/`, I drag them through the machinery. What do you want to know?",

    },

  ]);

  const [input, setInput] = useState("");

  const [loading, setLoading] = useState(false);

  async function sendMessage() {

    const trimmed = input.trim();

    if (!trimmed || loading) return;

    const nextMessages: ChatMessage[] = [

      ...messages,

      { role: "user", content: trimmed },

    ];

    setMessages(nextMessages);

    setInput("");

    setLoading(true);

    try {

      const resp = await fetch("/api/cody/chat", {

        method: "POST",

        headers: { "Content-Type": "application/json" },

        body: JSON.stringify({

          messages: nextMessages.map((m) => ({

            role: m.role,

            content: m.content,

          })),

        }),

      });

      if (!resp.ok) throw new Error("Cody is not answering.");

      const data = await resp.json();

      const reply: string = data.reply ?? "(no reply)";

      setMessages((prev) => [

        ...prev,

        { role: "assistant", content: reply },

      ]);

    } catch (err) {

      setMessages((prev) => [

        ...prev,

        {

          role: "assistant",

          content:

            "Cody dropped a sack on that one. The chat backend might be down – check the orchestrator logs or Ollama service.",

        },

      ]);

    } finally {

      setLoading(false);

    }

  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {

    if (e.key === "Enter" && !e.shiftKey) {

      e.preventDefault();

      sendMessage();

    }

  }

  return (

    <div className="fixed bottom-4 right-4 z-40">

      {/* Toggle button */}

      <button

        type="button"

        onClick={() => setOpen((v) => !v)}

        className="flex items-center gap-2 rounded-full bg-neutral-900/90 border border-neutral-700 px-4 py-2 text-xs font-medium shadow-lg hover:bg-neutral-800 transition"

      >

        <CodyMascot size="sm" />

        <span>{open ? "Close Cody chat" : "Chat with Cody"}</span>

      </button>

      {/* Panel */}

      {open && (

        <div className="mt-3 w-[320px] sm:w-[380px] rounded-2xl border border-neutral-800 bg-neutral-950/95 shadow-2xl backdrop-blur flex flex-col max-h-[60vh] overflow-hidden">

          <div className="flex items-center gap-2 px-3 py-2 border-b border-neutral-800">

            <CodyMascot size="sm" />

            <div className="flex flex-col">

              <span className="text-xs font-semibold">Cody the Cherry Picker</span>

              <span className="text-[11px] text-neutral-400">

                Ask how to use FileCherry, read logs, or fix stuff.

              </span>

            </div>

          </div>

          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2 text-xs">

            {messages.map((m, idx) => (

              <div

                key={idx}

                className={`flex ${

                  m.role === "user" ? "justify-end" : "justify-start"

                }`}

              >

                <div

                  className={`max-w-[85%] rounded-2xl px-3 py-2 ${

                    m.role === "user"

                      ? "bg-amber-400 text-neutral-950"

                      : "bg-neutral-900 text-neutral-100 border border-neutral-800"

                  } whitespace-pre-wrap`}

                >

                  {m.content}

                </div>

              </div>

            ))}

            {loading && (

              <div className="text-[11px] text-neutral-500">

                Cody is thinking really hard for someone with dot eyes…

              </div>

            )}

          </div>

          <div className="border-t border-neutral-800 p-2">

            <textarea

              value={input}

              onChange={(e) => setInput(e.target.value)}

              onKeyDown={handleKeyDown}

              rows={2}

              className="w-full resize-none rounded-xl bg-neutral-900 text-xs text-neutral-100 px-3 py-2 outline-none border border-neutral-700 focus:border-amber-400"

              placeholder=""Cody, why did that job fail?" or "How do I structure inputs for car photos?""

            />

            <div className="flex justify-end pt-1">

              <button

                type="button"

                onClick={sendMessage}

                disabled={loading || !input.trim()}

                className="rounded-full bg-amber-400 text-neutral-950 text-[11px] font-semibold px-3 py-1.5 disabled:opacity-60 disabled:cursor-not-allowed hover:bg-amber-300 transition"

              >

                {loading ? "Working..." : "Send"}

              </button>

            </div>

          </div>

        </div>

      )}

    </div>

  );

}

```

### 5.2 Wire It Into the App Shell

In your main app layout (the one for the appliance UI, not the landing page repo):

```tsx

// apps/ui/app/(app)/layout.tsx (or similar)

import type { ReactNode } from "react";

import { CodyChatPanel } from "@/components/CodyChatPanel";

export default function AppLayout({ children }: { children: ReactNode }) {

  return (

    <div className="min-h-screen bg-neutral-950 text-neutral-50">

      {/* existing header/nav */}

      {children}

      <CodyChatPanel />

    </div>

  );

}

```

Now every main app view has a "Chat with Cody" button in the corner.

---

## 6. Optional: Ghost-Posting Job Requests into Cody

Once the main "Action" form exists (where user describes what to do with files), we can:

* After a job is created successfully, POST to `/api/cody/chat` internally with a synthetic message:

  ```jsonc

  {

    "messages": [

      { "role": "user", "content": "I just asked you to: <user-intent>" }

    ]

  }

  ```

* Use Cody's reply as:

  * A friendly confirmation ("Got it, I'm running job 2025-11-21-A over your 84 files.")

  * A plain-language explanation of what's happening.

That message can be:

* appended automatically to the front-end chat history, and

* shown in the job detail screen as "Cody's commentary".

We **don't** wire job creation from chat yet – we just let Cody narrate.

---

## 7. Summary for Cursor

When you tell Cursor "add Cody chat", it should:

1. Create `config/llm/cody_system_prompt.md` with the persona text above.

2. Implement `CodyMessage` / `CodyChatRequest` / `CodyChatResponse` models.

3. Extend the Ollama client with `cody_chat(...)`.

4. Add a FastAPI route `POST /api/cody/chat`.

5. Add `CodyChatPanel` React component (UI code above).

6. Mount `CodyChatPanel` in the main app layout.

7. Verify:

   * Ollama reachable,

   * system prompt file readable,

   * chat works locally on `localhost:3000` inside the appliance UI.

After this, the OS layer has a fully in-character **"Chat with Cody"** sidekick that uses the same local LLM stack as the rest of FileCherry.

