import { WorkspacePage } from "@/features/workspace/workspace-page";
import { workspacePages } from "@/lib/content/workspace-pages";

export default function WorkspaceSimilarPage() {
  return <WorkspacePage content={workspacePages.similar} />;
}
