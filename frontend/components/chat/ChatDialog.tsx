"use client";

import { useEffect, useRef } from "react";
import { ChatPanel } from "./ChatPanel";
import { useChat } from "./ChatProvider";

// A native modal <dialog> gives focus trapping, Escape-to-close and focus restoration.
export function ChatDialog() {
  const { open, closeChat } = useChat();
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    document.documentElement.style.overflow = open ? "hidden" : "";
    return () => {
      document.documentElement.style.overflow = "";
    };
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      onClose={closeChat}
      aria-label="Chat with the digital twin"
      className="fixed inset-0 m-0 h-dvh max-h-none w-dvw max-w-none border-0 bg-paper p-0 text-ink"
    >
      {open ? <ChatPanel onClose={closeChat} /> : null}
    </dialog>
  );
}
