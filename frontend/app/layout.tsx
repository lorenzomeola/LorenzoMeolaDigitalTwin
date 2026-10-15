import type { Metadata } from "next";
import { Fraunces, Instrument_Sans, JetBrains_Mono } from "next/font/google";
import { ChatDialog } from "@/components/chat/ChatDialog";
import { ChatProvider } from "@/components/chat/ChatProvider";
import { SiteNav } from "@/components/SiteNav";
import { profile } from "@/lib/content";
import "./globals.css";

const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin"], axes: ["opsz"] });
const instrument = Instrument_Sans({ variable: "--font-instrument", subsets: ["latin"] });
const jetbrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });

export const metadata: Metadata = {
  title: `${profile.name} - ${profile.headline}`,
  description: profile.tagline,
  // Only production should be indexed; previews and local runs stay out of search results.
  robots:
    process.env.VERCEL_ENV === "production" ? { index: true, follow: true } : { index: false, follow: false },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${fraunces.variable} ${instrument.variable} ${jetbrains.variable} h-full`}
    >
      <body className="flex min-h-full flex-col">
        <ChatProvider>
          <SiteNav />
          <div className="flex-1">{children}</div>
          <footer className="mx-auto w-full max-w-5xl px-6 py-10 font-mono text-xs text-ink-soft">
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-6">
              <span>{profile.name}</span>
              <span className="flex gap-5">
                <a className="hover:text-accent" href={profile.links.github} rel="noreferrer" target="_blank">
                  GitHub
                </a>
                {profile.links.linkedin ? (
                  <a className="hover:text-accent" href={profile.links.linkedin} rel="noreferrer" target="_blank">
                    LinkedIn
                  </a>
                ) : null}
                <a className="hover:text-accent" href="/cv.pdf" download>
                  CV (PDF)
                </a>
              </span>
            </div>
          </footer>
          <ChatDialog />
        </ChatProvider>
      </body>
    </html>
  );
}
