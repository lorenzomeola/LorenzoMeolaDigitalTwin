"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
}

export interface ProviderOption {
  id: string;
  label: string;
  models: string[];
}

interface ProvidersResponse {
  providers: ProviderOption[];
  default: { provider: string; model: string } | null;
}

interface ChatState {
  open: boolean;
  openChat: () => void;
  closeChat: () => void;
  messages: ChatMessage[];
  sending: boolean;
  error: string | null;
  providers: ProviderOption[] | null;
  provider: string;
  model: string;
  selectProvider: (provider: string) => void;
  selectModel: (model: string) => void;
  contactConsent: boolean;
  setContactConsent: (value: boolean) => void;
  send: (text: string) => Promise<void>;
  reset: () => void;
}

const ChatContext = createContext<ChatState | null>(null);
const MAX_HISTORY = 40;
const MAX_HISTORY_CHARS = 60_000;
const STORAGE_KEY = "twin-chat-session-v1";

interface StoredSession {
  messages: ChatMessage[];
  contactConsent: boolean;
  provider: string;
  model: string;
}

function readSession(): StoredSession | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    const session = JSON.parse(stored) as StoredSession;
    const valid = Array.isArray(session.messages) && session.messages.every(
      (message) =>
        typeof message.id === "number" &&
        (message.role === "user" || message.role === "assistant") &&
        typeof message.content === "string",
    );
    return valid ? session : null;
  } catch {
    return null;
  }
}

function recentHistory(messages: ChatMessage[]) {
  const kept: { role: ChatMessage["role"]; content: string }[] = [];
  let total = 0;
  for (const { role, content } of messages.slice(-MAX_HISTORY).reverse()) {
    total += content.length;
    if (total > MAX_HISTORY_CHARS) break;
    kept.unshift({ role, content });
  }
  return kept;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used inside ChatProvider");
  return context;
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [session] = useState(readSession);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(() => session?.messages ?? []);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [providers, setProviders] = useState<ProviderOption[] | null>(null);
  const [provider, setProvider] = useState(session?.provider || "openai");
  const [model, setModel] = useState(session?.model ?? "");
  const [contactConsent, setContactConsent] = useState(session?.contactConsent ?? false);
  const nextId = useRef(Math.max(0, ...(session?.messages ?? []).map((message) => message.id)) + 1);
  const messagesRef = useRef<ChatMessage[]>(session?.messages ?? []);
  const loadedProviders = useRef(false);
  const restoredModel = useRef(Boolean(session?.model));

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ messages, contactConsent, provider, model } satisfies StoredSession),
      );
    } catch {
      // Storage can be unavailable or full; the chat still works without persistence.
    }
  }, [messages, contactConsent, provider, model]);

  const loadProviders = useCallback(async () => {
    if (loadedProviders.current) return;
    loadedProviders.current = true;
    try {
      const response = await fetch("/api/providers");
      const data = (await response.json()) as ProvidersResponse;
      setProviders(data.providers);
      if (data.default && !restoredModel.current) {
        setProvider(data.default.provider);
        setModel(data.default.model);
      }
    } catch {
      loadedProviders.current = false;
      setProviders([]);
    }
  }, []);

  const openChat = useCallback(() => {
    setOpen(true);
    void loadProviders();
  }, [loadProviders]);

  const closeChat = useCallback(() => setOpen(false), []);

  const selectProvider = useCallback(
    (next: string) => {
      setProvider(next);
      const option = providers?.find((entry) => entry.id === next);
      if (option) setModel(option.models[0]);
    },
    [providers],
  );

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || sending) return;

      const history = recentHistory(messagesRef.current);
      const userMessage: ChatMessage = { id: nextId.current++, role: "user", content };
      setMessages((current) => [...current, userMessage]);
      setSending(true);
      setError(null);

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: content,
            history,
            provider,
            model: model || undefined,
            contactConsent,
          }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || typeof data.reply !== "string") {
          throw new Error(
            typeof data.detail === "string" ? data.detail : "The twin could not answer.",
          );
        }
        setMessages((current) => [
          ...current,
          { id: nextId.current++, role: "assistant", content: data.reply },
        ]);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Something went wrong.");
      } finally {
        setSending(false);
      }
    },
    [contactConsent, model, provider, sending],
  );

  const reset = useCallback(() => {
    setMessages([]);
    setError(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore unavailable storage.
    }
  }, []);

  const value = useMemo<ChatState>(
    () => ({
      open,
      openChat,
      closeChat,
      messages,
      sending,
      error,
      providers,
      provider,
      model,
      selectProvider,
      selectModel: setModel,
      contactConsent,
      setContactConsent,
      send,
      reset,
    }),
    [
      open,
      openChat,
      closeChat,
      messages,
      sending,
      error,
      providers,
      provider,
      model,
      selectProvider,
      contactConsent,
      send,
      reset,
    ],
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}
