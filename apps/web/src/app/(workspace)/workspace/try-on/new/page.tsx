import { WorkspacePage } from "@/features/workspace/workspace-page";
import { workspacePages } from "@/lib/content/workspace-pages";

export default function WorkspaceNewTryOnPage() {
  return <WorkspacePage content={workspacePages.newTryOn} />;
}
