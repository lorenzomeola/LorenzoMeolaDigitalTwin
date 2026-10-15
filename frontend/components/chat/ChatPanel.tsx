"use client";

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { profile } from "@/lib/content";
import { useChat } from "./ChatProvider";

const SUGGESTIONS = [
  "What is your background?",
  "Tell me about the MatchKeeper project",
  "What do you do at Volvo Group?",
  "Which AI tools do you work with?",
];

export function ChatPanel({ onClose }: { onClose?: () => void }) {
  const chat = useChat();
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chat.messages.length, chat.sending, chat.error]);

  const hasProviders = chat.providers === null || chat.providers.length > 0;
  const currentProvider = chat.providers?.find((entry) => entry.id === chat.provider);

  function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!draft.trim() || chat.sending) return;
    const text = draft;
    setDraft("");
    void chat.send(text);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col bg-paper text-ink">
      <header className="flex items-center justify-between gap-4 border-b border-rule px-5 py-3.5 sm:px-8">
        <div>
          <p className="font-display text-xl leading-none">Ask {profile.name.split(" ")[0]}&apos;s twin</p>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-ink-soft">
            AI assistant - not Lorenzo himself
          </p>
        </div>
        <div className="flex items-center gap-2">
          {chat.messages.length > 0 ? (
            <button
              type="button"
              onClick={chat.reset}
              className="rounded-full border border-rule px-3 py-1.5 font-mono text-xs text-ink-soft transition hover:border-accent hover:text-accent"
            >
              New chat
            </button>
          ) : null}
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              aria-label="Close chat"
              className="grid h-9 w-9 place-items-center rounded-full border border-rule text-lg leading-none transition hover:border-accent hover:text-accent"
            >
              <span aria-hidden="true">&times;</span>
            </button>
          ) : null}
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-6 sm:px-8" aria-live="polite">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          <Bubble role="assistant">
            Hi, I&apos;m an AI twin of {profile.name}. Ask me about his work, projects and skills, and I&apos;ll
            only answer from what he has actually shared.
          </Bubble>

          {chat.messages.length === 0 ? (
            <div className="flex flex-wrap gap-2" role="group" aria-label="Suggested questions">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  disabled={chat.sending || !hasProviders}
                  onClick={() => void chat.send(suggestion)}
                  className="rounded-full border border-rule bg-paper-2 px-4 py-2 text-left text-sm transition hover:border-accent hover:text-accent disabled:opacity-50"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          ) : null}

          {chat.messages.map((message) => (
            <Bubble key={message.id} role={message.role}>
              {message.role === "assistant" ? (
                <div className="prose-chat">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                </div>
              ) : (
                message.content
              )}
            </Bubble>
          ))}

          {chat.sending ? (
            <Bubble role="assistant">
              <span className="inline-flex gap-1.5 py-1" role="status" aria-label="The twin is typing">
                {[0, 1, 2].map((index) => (
                  <span
                    key={index}
                    className="dot h-2 w-2 rounded-full bg-ink-soft"
                    style={{ animationDelay: `${index * 160}ms` }}
                  />
                ))}
              </span>
            </Bubble>
          ) : null}

          {chat.error ? (
            <p role="alert" className="rounded-xl border border-accent/50 bg-paper-2 px-4 py-3 text-sm">
              {chat.error}
            </p>
          ) : null}

          {chat.providers !== null && chat.providers.length === 0 ? (
            <p role="alert" className="rounded-xl border border-rule bg-paper-2 px-4 py-3 text-sm">
              The chat service is offline right now. You can still browse the site and download the CV.
            </p>
          ) : null}
          <div ref={endRef} />
        </div>
      </div>

      <form onSubmit={submit} className="border-t border-rule px-5 py-4 sm:px-8">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-3 rounded-2xl border border-rule bg-paper-2 p-2 focus-within:border-accent">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              maxLength={4000}
              placeholder="Ask anything about Lorenzo's work..."
              aria-label="Message"
              className="max-h-40 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-[15px] outline-none placeholder:text-ink-soft"
            />
            <button
              type="submit"
              disabled={!draft.trim() || chat.sending || !hasProviders}
              className="h-11 rounded-xl bg-accent px-5 text-sm font-medium text-accent-ink transition hover:opacity-90 disabled:opacity-40"
            >
              Send
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-2 font-mono text-[11px] text-ink-soft">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={chat.contactConsent}
                onChange={(event) => chat.setContactConsent(event.target.checked)}
                className="accent-[var(--accent)]"
              />
              <span>Allow the twin to save my email if I share it, so Lorenzo can reply</span>
            </label>

            {chat.providers && chat.providers.length > 0 ? (
              <span className="flex items-center gap-2">
                <select
                  aria-label="AI provider"
                  value={chat.provider}
                  onChange={(event) => chat.selectProvider(event.target.value)}
                  className="rounded-md border border-rule bg-paper px-2 py-1"
                >
                  {chat.providers.map((entry) => (
                    <option key={entry.id} value={entry.id}>
                      {entry.label}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Model"
                  value={chat.model}
                  onChange={(event) => chat.selectModel(event.target.value)}
                  className="max-w-48 rounded-md border border-rule bg-paper px-2 py-1"
                >
                  {(currentProvider?.models ?? []).map((entry) => (
                    <option key={entry} value={entry}>
                      {entry}
                    </option>
                  ))}
                </select>
              </span>
            ) : null}
          </div>
        </div>
      </form>
    </div>
  );
}

function Bubble({ role, children }: { role: "user" | "assistant"; children: React.ReactNode }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[88%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed ${
          isUser ? "whitespace-pre-wrap bg-accent text-accent-ink" : "border border-rule bg-paper-2"
        }`}
      >
        {children}
      </div>
    </div>
  );
}
