"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, MessageSquare } from "lucide-react";
import { useChat } from "@/components/chat/ChatProvider";
import { profile } from "@/lib/content";

const LINKS = [
  { href: "/", label: "About" },
  { href: "/resume", label: "Resume" },
  { href: "/projects", label: "Projects" },
];

export function SiteNav() {
  const pathname = usePathname();
  const { openChat } = useChat();

  return (
    <header className="site-header">
      <nav aria-label="Primary" className="site-shell site-nav">
        <Link href="/" className="site-brand" aria-label={`${profile.name}, home`}>
          <span className="brand-mark" aria-hidden="true">lm<span>.</span></span>
          <span className="brand-name">{profile.name}</span>
        </Link>
        <ul className="nav-links">
          {LINKS.map((link) => {
            const current = pathname === link.href;
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  aria-current={current ? "page" : undefined}
                  className={`nav-link ${current ? "is-current" : ""}`}
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
          <li>
            {pathname === "/chat" ? (
              <span
                aria-current="page"
                className="nav-chat"
              >
                <MessageSquare size={15} aria-hidden="true" /> <span>Chat</span>
              </span>
            ) : (
              <button
                type="button"
                onClick={openChat}
                className="nav-chat"
              >
                <MessageSquare size={15} aria-hidden="true" /> <span>Chat</span>
                <ArrowUpRight size={14} className="nav-chat-arrow" aria-hidden="true" />
              </button>
            )}
          </li>
        </ul>
      </nav>
    </header>
  );
}
