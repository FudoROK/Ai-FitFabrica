"use client";

import type { ComponentProps, ReactNode } from "react";
import { SiteButton } from "@/components/site/site-button";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import type { WorkspaceCapability } from "@/lib/api/contracts";

type WorkspaceCapabilityCtaProps = {
  capability: WorkspaceCapability;
  children: ReactNode;
  className?: string;
  href: string;
  showReason?: boolean;
  variant?: ComponentProps<typeof SiteButton>["variant"];
};

export function WorkspaceCapabilityCta({
  capability,
  children,
  className,
  href,
  showReason = true,
  variant,
}: WorkspaceCapabilityCtaProps) {
  const { bootstrap, hasCapability } = useWorkspaceRuntime();
  const enabled = hasCapability(capability);
  const reason = bootstrap?.quick_actions.find((action) => action.capability === capability)?.disabled_reason
    ?? "Действие временно недоступно для этого workspace.";

  if (enabled) {
    return <SiteButton className={className} href={href} variant={variant}>{children}</SiteButton>;
  }

  return (
    <span className={className}>
      <SiteButton className="w-full cursor-not-allowed opacity-60" disabled title={reason} variant={variant}>
        {children}
      </SiteButton>
      {showReason ? <span className="workspace-meta mt-2 block">{reason}</span> : null}
    </span>
  );
}
