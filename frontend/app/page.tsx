import Link from "next/link";
import { OpenChatButton } from "@/components/chat/OpenChatButton";
import { profile, projects } from "@/lib/content";

export default function AboutPage() {
  const current = profile.experience[0];

  return (
    <main className="mx-auto max-w-5xl px-6 pb-16 pt-14 sm:pt-20">
      <p className="rise font-mono text-xs uppercase tracking-[0.2em] text-accent" style={{ "--i": 0 } as React.CSSProperties}>
        {profile.headline} - {profile.location}
      </p>
      <h1
        className="rise mt-5 max-w-4xl font-display text-5xl leading-[1.02] tracking-tight sm:text-7xl"
        style={{ "--i": 1 } as React.CSSProperties}
      >
        I build products with AI, and I check every line it writes.
      </h1>
      <p
        className="rise mt-7 max-w-2xl text-lg leading-relaxed text-ink-soft"
        style={{ "--i": 2 } as React.CSSProperties}
      >
        {profile.tagline} I&apos;m an automotive engineer with an MSc in AI and machine learning, now looking for
        an {profile.careerGoal} role.
      </p>
      <div className="rise mt-9 flex flex-wrap items-center gap-3" style={{ "--i": 3 } as React.CSSProperties}>
        <OpenChatButton className="rounded-full bg-accent px-6 py-3 font-medium text-accent-ink transition hover:opacity-90">
          Talk to my digital twin
        </OpenChatButton>
        <Link
          href="/projects"
          className="rounded-full border border-rule px-6 py-3 transition hover:border-accent hover:text-accent"
        >
          See my projects
        </Link>
      </div>

      <section className="mt-20 grid gap-px overflow-hidden rounded-2xl border border-rule bg-rule sm:grid-cols-3">
        <div className="bg-paper p-6">
          <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">Right now</p>
          <p className="mt-3 font-display text-xl leading-snug">{current.role}</p>
          <p className="mt-1 text-sm text-ink-soft">
            {current.company} - since Jan 2026
          </p>
        </div>
        <div className="bg-paper p-6">
          <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">Studied</p>
          <p className="mt-3 font-display text-xl leading-snug">{profile.education[0].field}</p>
          <p className="mt-1 text-sm text-ink-soft">{profile.education[0].institution}</p>
        </div>
        <div className="bg-paper p-6">
          <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">Working with</p>
          <p className="mt-3 font-display text-xl leading-snug">Claude Code, Codex, FastAPI, Next.js</p>
          <p className="mt-1 text-sm text-ink-soft">Python and React: read, reason, validate</p>
        </div>
      </section>

      <section className="mt-20">
        <div className="flex items-end justify-between gap-4">
          <h2 className="font-display text-3xl">Selected work</h2>
          <Link href="/projects" className="font-mono text-sm text-accent hover:underline">
            All projects
          </Link>
        </div>
        <ul className="mt-6 divide-y divide-rule border-y border-rule">
          {projects.map((project) => (
            <li key={project.slug}>
              <Link
                href="/projects"
                className="group flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-5 transition hover:text-accent"
              >
                <span className="font-display text-xl">{project.title.split(" | ")[0]}</span>
                <span className="font-mono text-xs text-ink-soft group-hover:text-accent">
                  {project.kind} - {project.statusShort}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
