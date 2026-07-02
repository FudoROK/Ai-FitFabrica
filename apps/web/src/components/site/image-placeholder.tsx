type ImagePlaceholderProps = {
  className?: string;
  label?: string;
  accent?: "violet" | "sand" | "dark";
  split?: boolean;
  chips?: string[];
};

function getAccentClasses(accent: NonNullable<ImagePlaceholderProps["accent"]>): string {
  switch (accent) {
    case "dark":
      return "from-[#1f1c1b] via-[#45413e] to-[#90877d]";
    case "violet":
      return "from-[#f4f0ff] via-[#e6dbff] to-[#d8c3a5]";
    default:
      return "from-[#f4ebdc] via-[#e8d8be] to-[#b59a7a]";
  }
}

export function ImagePlaceholder({
  className,
  label,
  accent = "sand",
  split = false,
  chips = []
}: ImagePlaceholderProps) {
  return (
    <div className={`site-placeholder media-zoom rounded-[2rem] transition-transform duration-700 ease-out hover:scale-[1.015] ${className ?? ""}`.trim()}>
      <div className={`absolute inset-0 bg-gradient-to-br ${getAccentClasses(accent)}`} />
      {split ? <div className="absolute inset-y-0 left-1/2 w-px bg-white/50" /> : null}
      <div className="absolute inset-x-8 bottom-8 z-10 flex flex-wrap gap-2">
        {chips.map((chip) => (
          <span
            className="rounded-full bg-white/88 px-4 py-2 text-sm font-medium text-[var(--text-primary)] shadow-sm"
            key={chip}
          >
            {chip}
          </span>
        ))}
      </div>
      {label ? (
        <div className="absolute inset-0 z-10 flex items-center justify-center">
          <span className="rounded-full bg-white/88 px-5 py-3 text-sm font-semibold text-[var(--text-primary)] shadow-sm">
            {label}
          </span>
        </div>
      ) : null}
    </div>
  );
}
