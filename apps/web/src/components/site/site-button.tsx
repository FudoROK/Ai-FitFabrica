import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { MaterialIcon } from "@/components/site/material-icon";

type SiteButtonVariant = "primary" | "secondary" | "violet" | "soft" | "ghost";

type SharedProps = {
  children: ReactNode;
  className?: string;
  icon?: string;
  href?: string;
  variant?: SiteButtonVariant;
};

type SiteButtonProps = SharedProps & ButtonHTMLAttributes<HTMLButtonElement>;

function getVariantClasses(variant: SiteButtonVariant): string {
  switch (variant) {
    case "secondary":
    case "violet":
    case "soft":
    case "ghost":
    default:
      return "site-pill-button";
  }
}

function getCommonClasses(variant: SiteButtonVariant, className?: string): string {
  return [
    "inline-flex",
    getVariantClasses(variant),
    className ?? ""
  ].join(" ");
}

function ButtonContent({
  children,
  icon
}: {
  children: ReactNode;
  icon?: string;
}) {
  return (
    <>
      {icon ? <MaterialIcon className="text-[1.15rem]" name={icon} /> : null}
      <span>{children}</span>
    </>
  );
}

export function SiteButton(props: SiteButtonProps) {
  const variant = props.variant ?? "primary";

  if (typeof props.href === "string") {
    const { children, className, href, icon } = props;

    return (
      <Link className={getCommonClasses(variant, className)} href={href}>
        <ButtonContent icon={icon}>{children}</ButtonContent>
      </Link>
    );
  }

  const { children, className, href, icon, type = "button", ...buttonProps } = props;
  void href;

  return (
    <button
      {...buttonProps}
      className={getCommonClasses(variant, className)}
      type={type}
    >
      <ButtonContent icon={icon}>{children}</ButtonContent>
    </button>
  );
}
