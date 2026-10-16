import type { Metadata, Viewport } from "next";
import { Sora, Instrument_Sans, JetBrains_Mono } from "next/font/google";
import { ChatDialog } from "@/components/chat/ChatDialog";
import { ChatProvider } from "@/components/chat/ChatProvider";
import { SiteNav } from "@/components/SiteNav";
import { profile } from "@/lib/content";
import "./globals.css";

const sora = Sora({ variable: "--font-sora", subsets: ["latin"] });
const instrument = Instrument_Sans({ variable: "--font-instrument", subsets: ["latin"] });
const jetbrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  interactiveWidget: "resizes-content",
  themeColor: "#090b0e",
  colorScheme: "dark",
};

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
      className={`${sora.variable} ${instrument.variable} ${jetbrains.variable} h-full`}
    >
      <body className="flex min-h-full flex-col">
        <ChatProvider>
          <a href="#main-content" className="skip-link">Skip to content</a>
          <SiteNav />
          <div className="flex-1">{children}</div>
          <footer className="site-shell site-footer">
            <div className="footer-inner">
              <span>{profile.name} <span className="text-signal">/</span> {profile.location}</span>
              <span className="footer-links">
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
