import type { Metadata } from "next";
import { Download } from "lucide-react";
import { profile } from "@/lib/content";

export const metadata: Metadata = { title: `Resume - ${profile.name}` };

export default function ResumePage() {
  return (
    <main id="main-content" className="site-shell page-content">
      <div className="section-topline">
        <div><p className="eyebrow">Career & qualifications</p><h1 className="page-title mt-3">Resume</h1></div>
        <a
          href="/cv.pdf"
          download
          className="action-button secondary"
        >
          <Download size={16} aria-hidden="true" /> Download CV
        </a>
      </div>

      <section className="section-band">
        <SectionTitle>Experience</SectionTitle>
        <ol className="resume-timeline">
          {profile.experience.map((job) => (
            <li key={`${job.company}-${job.period}`} className="resume-item">
              <p className="font-mono text-xs text-ink-soft sm:pt-2">{job.period}</p>
              <div>
                <h3 className="resume-role">{job.role}</h3>
                <p className="mt-1 text-sm text-signal">{job.company}</p>
                <ul className="resume-highlights">
                  {job.highlights.map((highlight) => (
                    <li key={highlight}>{highlight}</li>
                  ))}
                </ul>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="section-band">
        <SectionTitle>Education</SectionTitle>
        <ul className="mt-6 space-y-6">
          {profile.education.map((item) => (
            <li key={item.institution} className="grid gap-1 sm:grid-cols-[11rem_1fr] sm:gap-8">
              <p className="font-mono text-xs text-ink-soft sm:pt-1.5">{item.period}</p>
              <div>
                <h3 className="resume-role">{item.field}</h3>
                <p className="mt-1 text-sm text-ink-soft">
                  {item.institution}, {item.location}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="section-band">
        <SectionTitle>Skills</SectionTitle>
        <div className="mt-6 grid gap-8 sm:grid-cols-2">
          {profile.skills.map((group) => (
            <div key={group.group}>
              <h3 className="text-sm font-medium text-ink">{group.group}</h3>
              <ul className="mt-3 flex flex-wrap gap-2">
                {group.items.map((item) => (
                  <li key={item} className="tech-tag">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="section-band grid gap-8 sm:grid-cols-2">
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
    <h2 className="eyebrow pb-2">
      {children}
    </h2>
  );
}
