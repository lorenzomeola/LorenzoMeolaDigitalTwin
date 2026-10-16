import profileJson from "@/content/profile.json";
import projectsJson from "@/content/projects.json";

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

export const profile = profileJson as unknown as Profile;
export const projects = projectsJson as unknown as Project[];
