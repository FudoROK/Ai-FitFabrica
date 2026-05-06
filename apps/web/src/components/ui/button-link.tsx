import Link from "next/link";
import type { PageAction } from "@/types/site";

type ButtonLinkProps = {
  action: PageAction;
};

export function ButtonLink({ action }: ButtonLinkProps) {
  const isPrimary = action.variant !== "secondary";
  const className = isPrimary ? "button button-primary" : "button button-secondary";

  return (
    <Link className={className} href={action.href}>
      {action.label}
    </Link>
  );
}
