export type NavRoute = {
  href: string;
  label: string;
};

export type PageSection = {
  title: string;
  body: string;
};

export type PageAction = {
  href: string;
  label: string;
  variant?: "primary" | "secondary";
};

export type PageMetric = {
  label: string;
  value: string;
};

export type PagePlaceholder = {
  eyebrow: string;
  title: string;
  body: string;
  items: string[];
};

export type PageCta = {
  title: string;
  body: string;
  action: PageAction;
};

export type PublicPageContent = {
  eyebrow: string;
  title: string;
  lead: string;
  actions: PageAction[];
  metrics: PageMetric[];
  highlights: PageSection[];
  steps: PageSection[];
  placeholder: PagePlaceholder;
  cta: PageCta;
};

export type WorkspacePageContent = {
  eyebrow: string;
  title: string;
  lead: string;
  actions: PageAction[];
  status: PageMetric[];
  checklist: PageSection[];
  panels: PageSection[];
  placeholder: PagePlaceholder;
};
