import type { ReactNode } from "react";

interface TooltipProps {
  content: string;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
  delay?: number;
}

export default function Tooltip({
  content,
  children,
  position = "top",
  delay = 200,
}: TooltipProps) {
  return (
    <div className={`tooltip-wrapper tooltip-${position}`} data-delay={delay}>
      {children}
      <span className="tooltip-content">{content}</span>
    </div>
  );
}
