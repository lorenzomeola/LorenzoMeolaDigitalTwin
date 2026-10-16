"use client";

import type { ReactNode } from "react";
import { useChat } from "./ChatProvider";

export function OpenChatButton({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  const { openChat } = useChat();
  return (
    <button type="button" onClick={openChat} className={className}>
      {children}
    </button>
  );
}
