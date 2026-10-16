"use client";

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowUp, ArrowUpRight, Bot, ChevronDown, RotateCcw, UserRound, X } from "lucide-react";
import { profile } from "@/lib/content";
import { useChat } from "./ChatProvider";

const SUGGESTIONS = [
  "What has Lorenzo built?",
  "How does he work with AI?",
  "What does he do at Volvo?",
  "What experience fits an AI Engineer role?",
];

export function ChatPanel({ onClose }: { onClose?: () => void }) {
  const chat = useChat();
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "instant", block: "end" });
  }, [chat.messages.length, chat.sending, chat.error]);

  useEffect(() => {
    if (!inputRef.current) return;
    inputRef.current.style.height = "auto";
    inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 144)}px`;
  }, [draft]);

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
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="chat-workspace">
      <header className="chat-header">
        <div className="chat-identity">
          <span className="chat-identity-icon"><Bot size={21} aria-hidden="true" /></span>
          <div><p className="chat-heading">Lorenzo&apos;s digital twin</p><p className="chat-subheading">AI assistant, not Lorenzo</p></div>
        </div>
        <div className="chat-header-actions">
          {chat.messages.length > 0 ? (
            <button
              type="button"
              onClick={chat.reset}
              aria-label="New chat"
              title="New chat"
              className="icon-button"
            >
              <RotateCcw aria-hidden="true" />
            </button>
          ) : null}
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              aria-label="Close chat"
              title="Close chat"
              className="icon-button"
            >
              <X aria-hidden="true" />
            </button>
          ) : null}
        </div>
      </header>

      <div className="chat-scroll" aria-live="polite" aria-label="Conversation" role="log" aria-relevant="additions text">
        <div className="chat-thread">
          {chat.messages.length === 0 ? (
            <section className="chat-welcome">
              <p className="eyebrow">{profile.name} / {profile.location}</p>
              <h1>His work, in context<span>.</span></h1>
              <p className="chat-welcome-copy">Automotive engineering. An MSc in AI. Products built with AI coding agents.</p>
              <div className="chat-suggestions" role="group" aria-label="Suggested questions">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  disabled={chat.sending || !hasProviders}
                  onClick={() => void chat.send(suggestion)}
                  className="chat-suggestion"
                >
                  {suggestion}
                  <ArrowUpRight size={15} aria-hidden="true" />
                </button>
              ))}
              </div>
            </section>
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
              <span className="inline-flex items-center gap-2 py-1" role="status" aria-label="The twin is preparing a response">
                {[0, 1, 2].map((index) => (
                  <span
                    key={index}
                    className="dot h-2 w-2 rounded-full bg-ink-soft"
                    style={{ animationDelay: `${index * 160}ms` }}
                  />
                ))}
                <span className="ml-2 text-xs text-ink-soft">Preparing a response</span>
              </span>
            </Bubble>
          ) : null}

          {chat.error ? (
            <p role="alert" className="chat-notice">
              {chat.error}
            </p>
          ) : null}

          {chat.providers !== null && chat.providers.length === 0 ? (
            <p role="alert" className="chat-notice">
              The chat is unavailable. Lorenzo&apos;s CV and project pages are still available.
            </p>
          ) : null}
          <div ref={endRef} />
        </div>
      </div>

      <form onSubmit={submit} className="chat-composer">
        <div className="chat-composer-inner">
          <div className="chat-input-row">
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              maxLength={12000}
              placeholder="Ask about Lorenzo or paste a role..."
              aria-label="Message"
              enterKeyHint="send"
              className="chat-input"
            />
            <button
              type="submit"
              disabled={!draft.trim() || chat.sending || !hasProviders}
              aria-label="Send message"
              title="Send message"
              className="chat-send"
            >
              <ArrowUp size={20} aria-hidden="true" />
            </button>
          </div>

          <div className="chat-composer-options">
            <label className="chat-consent">
              <input
                type="checkbox"
                checked={chat.contactConsent}
                onChange={(event) => chat.setContactConsent(event.target.checked)}
                className="chat-consent-checkbox"
              />
              <span>I agree to saving my details, messages and interview requests so Lorenzo can reply.</span>
            </label>

            {chat.providers && chat.providers.length > 0 ? (
              <div className="chat-model-controls">
                <label className="chat-select-wrap"><span className="sr-only">AI provider</span><select
                  aria-label="AI provider"
                  value={chat.provider}
                  onChange={(event) => chat.selectProvider(event.target.value)}
                  className="chat-select chat-provider-select"
                >
                  {chat.providers.map((entry) => (
                    <option key={entry.id} value={entry.id}>
                      {entry.label}
                    </option>
                  ))}
                </select><ChevronDown size={13} aria-hidden="true" /></label>
                <label className="chat-select-wrap chat-model-wrap"><span className="sr-only">Model</span><select
                  aria-label="Model"
                  value={chat.model}
                  onChange={(event) => chat.selectModel(event.target.value)}
                  className="chat-select"
                >
                  {(currentProvider?.models ?? []).map((entry) => (
                    <option key={entry} value={entry}>
                      {entry}
                    </option>
                  ))}
                </select><ChevronDown size={13} aria-hidden="true" /></label>
              </div>
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
    <div className={`chat-message ${isUser ? "chat-message-user" : "chat-message-assistant"}`}>
      <span className="chat-message-avatar" aria-hidden="true">{isUser ? <UserRound size={16} /> : <Bot size={17} />}</span>
      <div className="chat-message-body">
        <p className="chat-message-author">{isUser ? "You" : "Lorenzo's twin"}</p>
        <div className="chat-message-content">
        {children}
        </div>
      </div>
    </div>
  );
}
