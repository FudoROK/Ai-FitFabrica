import { WorkspacePage } from "@/features/workspace/workspace-page";
import { workspacePages } from "@/lib/content/workspace-pages";

export default function WorkspaceDashboardPage() {
  return <WorkspacePage content={workspacePages.dashboard} />;
}
