import type { Metadata } from "next";
import { profile } from "@/lib/content";

export const metadata: Metadata = { title: `Resume - ${profile.name}` };

export default function ResumePage() {
  return (
    <main className="mx-auto max-w-5xl px-6 pb-16 pt-14 sm:pt-20">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-display text-5xl tracking-tight sm:text-6xl">Resume</h1>
        <a
          href="/cv.pdf"
          download
          className="rounded-full border border-rule px-5 py-2.5 text-sm transition hover:border-accent hover:text-accent"
        >
          Download CV (PDF)
        </a>
      </div>

      <section className="mt-14">
        <SectionTitle>Experience</SectionTitle>
        <ol className="mt-6 space-y-10">
          {profile.experience.map((job) => (
            <li key={`${job.company}-${job.period}`} className="grid gap-3 sm:grid-cols-[11rem_1fr] sm:gap-8">
              <p className="font-mono text-xs text-ink-soft sm:pt-2">{job.period}</p>
              <div>
                <h3 className="font-display text-2xl leading-snug">{job.role}</h3>
                <p className="text-ink-soft">{job.company}</p>
                <ul className="mt-3 list-disc space-y-2 pl-5 leading-relaxed">
                  {job.highlights.map((highlight) => (
                    <li key={highlight}>{highlight}</li>
                  ))}
                </ul>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-16">
        <SectionTitle>Education</SectionTitle>
        <ul className="mt-6 space-y-6">
          {profile.education.map((item) => (
            <li key={item.institution} className="grid gap-1 sm:grid-cols-[11rem_1fr] sm:gap-8">
              <p className="font-mono text-xs text-ink-soft sm:pt-1.5">{item.period}</p>
              <div>
                <h3 className="font-display text-xl">{item.field}</h3>
                <p className="text-ink-soft">
                  {item.institution}, {item.location}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-16">
        <SectionTitle>Skills</SectionTitle>
        <div className="mt-6 grid gap-8 sm:grid-cols-2">
          {profile.skills.map((group) => (
            <div key={group.group}>
              <h3 className="font-mono text-xs uppercase tracking-wider text-ink-soft">{group.group}</h3>
              <ul className="mt-3 flex flex-wrap gap-2">
                {group.items.map((item) => (
                  <li key={item} className="rounded-full border border-rule bg-paper-2 px-3 py-1.5 text-sm">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-16 grid gap-10 sm:grid-cols-2">
        <div>
          <SectionTitle>Languages</SectionTitle>
          <ul className="mt-6 space-y-2">
            {profile.languages.map((language) => (
              <li key={language.name} className="flex justify-between border-b border-rule pb-2">
                <span>{language.name}</span>
                <span className="font-mono text-sm text-ink-soft">{language.level}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <SectionTitle>Certificates</SectionTitle>
          <ul className="mt-6 space-y-2">
            {profile.certificates.map((certificate) => (
              <li key={certificate} className="border-b border-rule pb-2">
                {certificate}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="border-b border-rule pb-3 font-mono text-xs uppercase tracking-[0.2em] text-accent">
      {children}
    </h2>
  );
}
