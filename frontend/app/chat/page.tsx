"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { useChat } from "@/components/chat/ChatProvider";

// /chat opens the same dialog session used elsewhere, and closing it returns home.
export default function ChatPage() {
  const { open, openChat, closeChat } = useChat();
  const router = useRouter();
  const wasOpen = useRef(false);

  useEffect(() => {
    openChat();
    return () => closeChat();
  }, [openChat, closeChat]);

  useEffect(() => {
    if (open) wasOpen.current = true;
    else if (wasOpen.current) router.replace("/");
  }, [open, router]);

  return <main id="main-content" className="min-h-[60dvh]" aria-hidden="true" />;
}
