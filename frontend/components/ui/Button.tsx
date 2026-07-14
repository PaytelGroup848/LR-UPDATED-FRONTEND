import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "primary" | "green" | "danger";
};

export function Button({ className = "", variant = "default", ...props }: ButtonProps) {
  const variantClass = variant === "default" ? "" : variant;

  return <button className={`btn ${variantClass} ${className}`.trim()} {...props} />;
}
