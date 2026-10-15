import type { Metadata } from "next";
import { profile, projects } from "@/lib/content";

export const metadata: Metadata = { title: `Projects - ${profile.name}` };

export default function ProjectsPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 pb-16 pt-14 sm:pt-20">
      <h1 className="font-display text-5xl tracking-tight sm:text-6xl">Projects</h1>
      <p className="mt-5 max-w-2xl text-lg leading-relaxed text-ink-soft">
        Three things I&apos;ve built or am building. Each one is labelled honestly: what it does, what state it is in,
        and what I did.
      </p>

      <div className="mt-14 space-y-10">
        {projects.map((project) => (
          <article key={project.slug} className="rounded-3xl border border-rule bg-paper-2/60 p-6 sm:p-9">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 font-mono text-[11px] uppercase tracking-wider">
              <span className="text-ink-soft">{project.kind}</span>
              <span className="rounded-full bg-accent px-3 py-1 text-accent-ink">{project.statusShort}</span>
            </div>
            <h2 className="mt-4 font-display text-3xl leading-tight sm:text-4xl">{project.title}</h2>
            <p className="mt-4 max-w-3xl text-lg leading-relaxed text-ink-soft">{project.summary}</p>

            {project.contributionConfirmed ? (
              <p className="mt-5 max-w-3xl leading-relaxed">
                <span className="font-mono text-xs uppercase tracking-wider text-accent">My part - </span>
                {project.contribution}
              </p>
            ) : null}

            <ul className="mt-6 grid gap-x-8 gap-y-3 sm:grid-cols-2">
              {project.highlights.map((highlight) => (
                <li key={highlight} className="relative pl-5 leading-relaxed before:absolute before:left-0 before:top-[0.7em] before:h-1.5 before:w-1.5 before:rounded-full before:bg-accent">
                  {highlight}
                </li>
              ))}
            </ul>

            <ul className="mt-7 flex flex-wrap gap-2">
              {project.technology.map((item) => (
                <li key={item} className="rounded-full border border-rule px-3 py-1 font-mono text-xs text-ink-soft">
                  {item}
                </li>
              ))}
            </ul>

            {project.links.length > 0 ? (
              <p className="mt-7 flex flex-wrap gap-x-6 gap-y-2">
                {project.links.map((link) => (
                  <a
                    key={link.url}
                    href={link.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-accent underline underline-offset-4"
                  >
                    {link.label} &rarr;
                  </a>
                ))}
              </p>
            ) : (
              <p className="mt-7 font-mono text-xs text-ink-soft">
                Internal Volvo Group work - no public link, data or screenshots.
              </p>
            )}
          </article>
        ))}
      </div>
    </main>
  );
}
