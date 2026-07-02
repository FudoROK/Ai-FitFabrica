import { WorkspaceShellEmpty } from "@/features/workspace/workspace-shell-empty";
import { WorkspaceShellError } from "@/features/workspace/workspace-shell-error";
import { WorkspaceShellLoading } from "@/features/workspace/workspace-shell-loading";

type WorkspaceShellStateProps = {
  error: string;
  hasBootstrap: boolean;
  isLoading: boolean;
  onRetry: () => Promise<void>;
};

export function WorkspaceShellState({
  error,
  hasBootstrap,
  isLoading,
  onRetry,
}: WorkspaceShellStateProps) {
  if (isLoading) {
    return <WorkspaceShellLoading />;
  }

  if (error) {
    return <WorkspaceShellError error={error} onRetry={onRetry} />;
  }

  if (!hasBootstrap) {
    return <WorkspaceShellEmpty />;
  }

  return null;
}
