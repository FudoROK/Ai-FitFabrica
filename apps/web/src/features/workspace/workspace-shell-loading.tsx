export function WorkspaceShellLoading() {
  return (
    <div className="px-6 py-8 lg:px-8 lg:py-10">
      <div className="site-card p-8 lg:p-10">
        <div className="h-5 w-32 rounded-full bg-[var(--surface-alt)]" />
        <div className="mt-5 h-12 w-full max-w-[420px] rounded-full bg-[var(--surface-alt)]" />
        <div className="mt-4 h-5 w-full max-w-[720px] rounded-full bg-[var(--surface-alt)]" />
        <div className="mt-10 grid gap-4 xl:grid-cols-4">
          <div className="h-[180px] rounded-[2rem] bg-[var(--surface-alt)]" />
          <div className="h-[180px] rounded-[2rem] bg-[var(--surface-alt)]" />
          <div className="h-[180px] rounded-[2rem] bg-[var(--surface-alt)]" />
          <div className="h-[180px] rounded-[2rem] bg-[var(--surface-alt)]" />
        </div>
      </div>
    </div>
  );
}
