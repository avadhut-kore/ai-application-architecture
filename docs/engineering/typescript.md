# TypeScript Engineering Standard

## 1. Baseline Runtime & Tooling Strategy

TypeScript is the repository's **primary language for web demonstration interfaces, streaming client applications, and lightweight Node.js gateway services**.

* **Runtime Baseline**: **Node.js 20 LTS** (or modern browser runtimes for frontends).
* **Language Baseline**: Modern ECMAScript / TypeScript with strict mode enabled (`"strict": true`).
* **Linter & Formatter**: **ESLint** (with `@typescript-eslint`) and **Prettier**.
* **Test Runner**: **Vitest** for fast, native TypeScript unit testing; **Playwright** for end-to-end browser testing where justified.
* **Runtime Schema Validator**: **Zod** for boundary payload validation.

---

## 2. Strict Type Safety & Compiler Options

* Every TypeScript project must include a strict `tsconfig.json`:
  ```json
  {
    "compilerOptions": {
      "target": "ES2022",
      "module": "NodeNext",
      "moduleResolution": "NodeNext",
      "strict": true,
      "noImplicitAny": true,
      "strictNullChecks": true,
      "noUncheckedIndexedAccess": true,
      "exactOptionalPropertyTypes": true,
      "skipLibCheck": true,
      "forceConsistentCasingInFileNames": true
    }
  }
  ```

### 2.1 The Ban on Unsafe `any`
* The `any` type is **strictly prohibited** in production code paths.
* When dealing with dynamic or unknown external payloads (e.g., raw JSON from an AI provider or webhook), use `unknown` and validate the structure using a **Zod** schema:
  ```typescript
  import { z } from "zod";

  export const ChatMessageSchema = z.object({
    role: z.enum(["user", "assistant", "system"]),
    content: z.string().min(1),
  });

  export type ChatMessage = z.infer<typeof ChatMessageSchema>;

  export function parseMessage(payload: unknown): ChatMessage {
    return ChatMessageSchema.parse(payload); // Throws ZodError if invalid
  }
  ```

---

## 3. Streaming & Async Patterns

### 3.1 Real-Time Streaming (SSE & WebSockets)
* Frontend clients consuming streaming LLM tokens must handle chunked Server-Sent Events (SSE) or WebSockets without buffering the entire message into memory:
  ```typescript
  export async function* streamLlmTokens(response: Response): AsyncGenerator<string, void, unknown> {
    const reader = response.body?.getReader();
    if (!reader) throw new Error("Response body is not readable");

    const decoder = new TextDecoder("utf-8");
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      yield decoder.decode(value, { stream: true });
    }
  }
  ```

### 3.2 Cancellation via AbortController
* All asynchronous fetch requests to AI endpoints must accept an `AbortSignal` to support user cancellation or barge-in interruption:
  ```typescript
  export async function fetchCompletion(prompt: string, signal?: AbortSignal): Promise<string> {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
      signal,
    });
    // ...
  }
  ```

---

## 4. Frontend State & Architecture

* **Differentiate Server State from UI State**: Use libraries like TanStack Query (React Query) for asynchronous server/model data, and lightweight local state (Zustand, React hooks) for ephemeral UI states (modal open, draft text).
* **XSS Prevention**: Never render raw model completions directly using `dangerouslySetInnerHTML` without rigorous HTML sanitization (DOMPurify).

---

## 5. Testing & Verification

* **Unit Testing**: Use `vitest` for testing state mappers, reducers, parsers, and custom hooks.
* **Component Testing**: Test UI components using `@testing-library/react`.
* **Mocking**: Use Mock Service Worker (`msw`) to mock HTTP and streaming endpoints in tests without hitting live networks.
