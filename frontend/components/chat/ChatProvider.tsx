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
const MAX_HISTORY = 20;

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used inside ChatProvider");
  return context;
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [providers, setProviders] = useState<ProviderOption[] | null>(null);
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [contactConsent, setContactConsent] = useState(false);
  const nextId = useRef(1);
  const messagesRef = useRef<ChatMessage[]>([]);
  const loadedProviders = useRef(false);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const loadProviders = useCallback(async () => {
    if (loadedProviders.current) return;
    loadedProviders.current = true;
    try {
      const response = await fetch("/api/providers");
      const data = (await response.json()) as ProvidersResponse;
      setProviders(data.providers);
      if (data.default) {
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

      const history = messagesRef.current
        .slice(-MAX_HISTORY)
        .map(({ role, content: body }) => ({ role, content: body }));
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
