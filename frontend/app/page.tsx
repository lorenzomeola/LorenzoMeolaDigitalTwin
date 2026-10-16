import Link from "next/link";
import Image from "next/image";
import { ArrowDownRight, ArrowRight, ArrowUpRight, Braces, CheckCheck, Cpu, Download, GitBranch, MessageSquare } from "lucide-react";
import { OpenChatButton } from "@/components/chat/OpenChatButton";
import { profile, projects } from "@/lib/content";

export default function AboutPage() {
  const current = profile.experience[0];

  return (
    <main id="main-content" className="site-shell page-content">
      <section className="intro-section" aria-labelledby="intro-title">
        <div className="intro-copy">
          <p className="eyebrow rise">{profile.headline} <span className="intro-location">/ {profile.location}</span></p>
          <h1 id="intro-title" className="intro-name rise">Lorenzo<br />Meola<span>.</span></h1>
          <p className="intro-statement rise">I build software with AI.<br /><span>I design it, review it, and test it.</span></p>
          <p className="body-copy intro-description rise">
            Automotive engineer with an MSc in AI and machine learning. I work with AI coding agents
            to build products, and I read and validate the code they produce. Looking for an {profile.careerGoal} role.
          </p>
          <div className="intro-actions rise">
            <OpenChatButton className="action-button"><MessageSquare size={17} aria-hidden="true" /> Talk to my twin <ArrowUpRight size={16} aria-hidden="true" /></OpenChatButton>
            <a href="/cv.pdf" download className="text-link"><Download size={16} aria-hidden="true" /> Download CV</a>
          </div>
        </div>
        <aside className="twin-flow rise" aria-label="Digital twin processing flow">
          <div className="flow-caption"><GitBranch size={16} aria-hidden="true" /><span>Digital twin / request flow</span><span className="flow-index">01</span></div>
          <ol className="flow-steps">
            <li><span className="flow-icon"><MessageSquare size={19} aria-hidden="true" /></span><div><strong>Your question</strong><span>Experience, projects or a role</span></div><span className="flow-step-number">01</span></li>
            <li><span className="flow-icon"><Cpu size={19} aria-hidden="true" /></span><div><strong>Profile + model</strong><span>CV and verified project records</span></div><span className="flow-step-number">02</span></li>
            <li><span className="flow-icon"><Braces size={19} aria-hidden="true" /></span><div><strong>Tools, when needed</strong><span>Role match, contact, messages</span></div><span className="flow-step-number">03</span></li>
            <li><span className="flow-icon flow-icon-orange"><CheckCheck size={19} aria-hidden="true" /></span><div><strong>Reviewed response</strong><span>Model output checked before delivery</span></div><span className="flow-step-number">04</span></li>
          </ol>
          <OpenChatButton className="flow-chat-link">Ask about my work <ArrowUpRight size={17} aria-hidden="true" /></OpenChatButton>
        </aside>
      </section>

      <section className="profile-strip" aria-label="Profile at a glance">
        <div><p className="strip-label">Current role</p><h2>{current.role}</h2><p>{current.company} / Jan 2026 to present</p></div>
        <div><p className="strip-label">Education</p><h2>{profile.education[0].field}</h2><p>{profile.education[0].institution}</p></div>
        <div><p className="strip-label">Working with</p><h2>Claude Code, Codex,<br className="hidden sm:block" /> FastAPI, Next.js</h2><p>Python and React: read, reason, validate</p></div>
      </section>

      <section className="section-band" aria-labelledby="selected-work-title">
        <div className="section-topline"><div><p className="eyebrow">Selected work</p><h2 id="selected-work-title" className="section-heading mt-2">From an idea to working software.</h2></div><Link href="/projects" className="text-link">View projects <ArrowRight size={16} aria-hidden="true" /></Link></div>
        <div className="work-overview">
          <figure className="product-preview">
            <Link href="/projects#ai-assets-directory" aria-label="View AI Assets Directory project">
              <Image src="/images/ai-assets-directory.webp" width={1200} height={800} unoptimized alt="AI Assets Directory website with its searchable collection of skills, agents and AI workflows" sizes="(max-width: 767px) 100vw, 50vw" />
            </Link>
            <figcaption><span>AI Assets Directory</span><span>Live product <ArrowUpRight size={14} aria-hidden="true" /></span></figcaption>
          </figure>
          <ul className="work-list">
            {projects.map((project, index) => (
              <li key={project.slug}><Link href={`/projects#${project.slug}`}><span className="work-number">0{index + 1}</span><div><span className="work-title">{project.title.split(" | ")[0]}</span><span className="work-meta">{project.kind} / {project.statusShort}</span></div><ArrowDownRight size={20} aria-hidden="true" /></Link></li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
