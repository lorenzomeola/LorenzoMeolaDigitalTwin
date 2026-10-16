import type { Metadata } from "next";
import { ArrowUpRight, LockKeyhole } from "lucide-react";
import { profile, projects } from "@/lib/content";

export const metadata: Metadata = { title: `Projects - ${profile.name}` };

export default function ProjectsPage() {
  return (
    <main id="main-content" className="site-shell page-content">
      <p className="eyebrow">Software I work on</p>
      <h1 className="page-title mt-3">Projects</h1>
      <p className="body-copy mt-4 text-[15px]">
        Internal analytics at Volvo, a directory of AI tools, and a football marketplace.
        My contribution and the current state of each project are listed below.
      </p>

      <div className="project-list">
        {projects.map((project, index) => (
          <article id={project.slug} key={project.slug} className="project-entry">
            <div className="project-meta"><span className="project-index">0{index + 1}</span><span>{project.kind}</span><span className="project-status">{project.statusShort}</span></div>
            <h2 className="project-title">{project.title}</h2>
            <p className="body-copy mt-4 text-[15px]">{project.summary}</p>

            {project.contributionConfirmed ? (
              <p className="project-contribution">
                <span className="text-accent">My work: </span>
                {project.contribution}
              </p>
            ) : null}

            <ul className="project-highlights">
              {project.highlights.map((highlight) => (
                <li key={highlight}>
                  <span aria-hidden="true" className="project-bullet" />{highlight}
                </li>
              ))}
            </ul>

            <ul className="mt-7 flex flex-wrap gap-2">
              {project.technology.map((item) => (
                <li key={item} className="tech-tag">
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
                    className="text-link"
                  >
                    {link.label} <ArrowUpRight size={15} aria-hidden="true" />
                  </a>
                ))}
              </p>
            ) : (
              <p className="project-private-note">
                <LockKeyhole size={14} aria-hidden="true" /> Internal Volvo Group work. No public data, screenshots or results.
              </p>
            )}
          </article>
        ))}
      </div>
    </main>
  );
}
