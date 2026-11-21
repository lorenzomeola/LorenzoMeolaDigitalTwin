import profileJson from "@/content/profile.json";
import projectsJson from "@/content/projects.json";
import coursesJson from "@/content/courses.json";

export interface Profile {
  name: string;
  headline: string;
  tagline: string;
  location: string;
  careerGoal: string;
  education: { institution: string; field: string; location: string; period: string }[];
  experience: { role: string; company: string; period: string; highlights: string[] }[];
  skills: { group: string; items: string[] }[];
  languages: { name: string; level: string }[];
  certificates: string[];
  links: { github: string; linkedin?: string };
}

export interface ProjectLink {
  label: string;
  url: string;
}

export interface Project {
  slug: string;
  title: string;
  status: string;
  statusShort: string;
  kind: string;
  summary: string;
  contribution: string;
  contributionConfirmed: boolean;
  technology: string[];
  highlights: string[];
  links: ProjectLink[];
}

export interface Course {
  slug: string;
  category: string;
  title: string;
  provider: string;
  instructors: string;
  status: "completed" | "in-progress";
  statusShort: string;
  completedOn?: string;
  hours: string;
  summary: string;
  syllabus: string[];
  projects: string[];
  technology: string[];
  courseUrl: string;
  verifyUrl?: string;
  certificateFile?: string;
}

export const profile = profileJson as unknown as Profile;
export const courses = coursesJson as unknown as Course[];
export const projects = projectsJson as unknown as Project[];
