"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
    <header className="sticky top-0 z-20 border-b border-rule bg-paper/85 backdrop-blur">
      <nav
        aria-label="Primary"
        className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-4"
      >
        <Link href="/" className="font-display text-lg leading-none">
          {profile.name}
        </Link>
        <ul className="flex items-center gap-1 text-sm sm:gap-2">
          {LINKS.map((link) => {
            const current = pathname === link.href;
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  aria-current={current ? "page" : undefined}
                  className={`rounded-full px-3 py-1.5 transition hover:text-accent ${
                    current ? "bg-paper-2 text-accent" : "text-ink-soft"
                  }`}
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
                className="rounded-full bg-accent px-4 py-1.5 font-medium text-accent-ink"
              >
                Chat
              </span>
            ) : (
              <button
                type="button"
                onClick={openChat}
                className="rounded-full bg-accent px-4 py-1.5 font-medium text-accent-ink transition hover:opacity-90"
              >
                Chat
              </button>
            )}
          </li>
        </ul>
      </nav>
    </header>
  );
}
