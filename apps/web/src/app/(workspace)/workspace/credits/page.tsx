import { WorkspacePage } from "@/features/workspace/workspace-page";
import { workspacePagesExtra } from "@/lib/content/workspace-pages-extra";

export default function WorkspaceCreditsPage() {
  return <WorkspacePage content={workspacePagesExtra.credits} />;
}
