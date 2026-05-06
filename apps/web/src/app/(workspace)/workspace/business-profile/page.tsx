import { WorkspacePage } from "@/features/workspace/workspace-page";
import { workspacePagesExtra } from "@/lib/content/workspace-pages-extra";

export default function WorkspaceBusinessProfilePage() {
  return <WorkspacePage content={workspacePagesExtra.businessProfile} />;
}
