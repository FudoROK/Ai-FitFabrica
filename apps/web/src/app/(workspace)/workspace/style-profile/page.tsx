import { WorkspacePage } from "@/features/workspace/workspace-page";
import { workspacePagesExtra } from "@/lib/content/workspace-pages-extra";

export default function WorkspaceStyleProfilePage() {
  return <WorkspacePage content={workspacePagesExtra.styleProfile} />;
}
