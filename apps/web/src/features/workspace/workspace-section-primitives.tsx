"use client";

import type { ReactNode } from "react";

type WorkspaceSectionCardProps = {
  children: ReactNode;
  title: string;
};

type WorkspaceActionCardProps = {
  children: ReactNode;
};

export function WorkspaceSectionCard({ children, title }: WorkspaceSectionCardProps) {
  return (
    <article className="site-card p-7 lg:p-8">
      <h2 className="workspace-section-title">{title}</h2>
      {children}
    </article>
  );
}

export function WorkspaceActionCard({ children }: WorkspaceActionCardProps) {
  return <article className="site-card p-7 lg:p-8">{children}</article>;
}
