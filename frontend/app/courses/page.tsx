import type { Metadata } from "next";
import fs from "node:fs";
import path from "node:path";
import { ArrowUpRight, Download } from "lucide-react";
import { courses, profile, type Course } from "@/lib/content";

export const metadata: Metadata = { title: `Courses - ${profile.name}` };

function fileExists(publicPath?: string) {
  return Boolean(publicPath) && fs.existsSync(path.join(process.cwd(), "public", publicPath!));
}

const CATEGORIES = ["AI Engineering", "Coding"];

function CourseEntry({ course, index }: { course: Course; index: number }) {
  return (
    <article id={course.slug} className="project-entry">
      <div className="project-meta">
        <span className="project-index">0{index + 1}</span>
        <span>{course.provider}</span>
        <span>{course.hours}</span>
        <span className="project-status">{course.statusShort}</span>
        {course.completedOn ? <span>{course.completedOn}</span> : null}
      </div>
      <h3 className="project-title">{course.title}</h3>
      <p className="body-copy mt-2 text-[13px]">Instructors: {course.instructors}</p>
      <p className="body-copy mt-4 text-[15px]">{course.summary}</p>

      <h4 className="eyebrow mt-7">Curriculum</h4>
      <ul className="project-highlights is-single-column">
        {course.syllabus.map((item) => (
          <li key={item}>
            <span aria-hidden="true" className="project-bullet" />{item}
          </li>
        ))}
      </ul>

      <h4 className="eyebrow mt-7">{course.status === "completed" ? "Projects built" : "Projects"}</h4>
      <ul className="project-highlights">
        {course.projects.map((item) => (
          <li key={item}>
            <span aria-hidden="true" className="project-bullet" />{item}
          </li>
        ))}
      </ul>

      <ul className="mt-7 flex flex-wrap gap-2">
        {course.technology.map((item) => (
          <li key={item} className="tech-tag">{item}</li>
        ))}
      </ul>

      <p className="mt-7 flex flex-wrap gap-x-6 gap-y-2">
        <a href={course.courseUrl} target="_blank" rel="noreferrer" className="text-link">
          View course <ArrowUpRight size={15} aria-hidden="true" />
        </a>
        {fileExists(course.certificateFile) ? (
          <a href={course.certificateFile} download className="text-link">
            Download certificate <Download size={15} aria-hidden="true" />
          </a>
        ) : null}
        {course.verifyUrl ? (
          <a href={course.verifyUrl} target="_blank" rel="noreferrer" className="text-link">
            Verify certificate <ArrowUpRight size={15} aria-hidden="true" />
          </a>
        ) : null}
      </p>
    </article>
  );
}

export default function CoursesPage() {
  return (
    <main id="main-content" className="site-shell page-content">
      <p className="eyebrow">Ongoing learning</p>
      <h1 className="page-title mt-3">Courses</h1>
      <p className="body-copy mt-4 text-[15px]">
        Courses I have taken or am taking, grouped by topic, with what each one covers, a link to the course
        and my certificate when I have finished it.
      </p>

      {CATEGORIES.map((category) => {
        const items = courses.filter((course) => course.category === category);
        if (items.length === 0) return null;
        return (
          <section key={category} aria-labelledby={`category-${category}`} className="course-group">
            <h2 id={`category-${category}`} className="course-category">{category}</h2>
            <div className="project-list">
              {items.map((course, index) => (
                <CourseEntry key={course.slug} course={course} index={index} />
              ))}
            </div>
          </section>
        );
      })}
    </main>
  );
}
