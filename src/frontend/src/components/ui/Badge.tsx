import React from "react";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline";
}

export const Badge: React.FC<BadgeProps> = ({ variant = "default", className, children, ...props }) => {
  const base = "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium";
  const variantClass = variant === "outline" ? "border border-gray-300 bg-white text-gray-900" : "bg-gray-200 text-gray-800";
  return (
    <span className={`${base} ${variantClass} ${className}`} {...props}>
      {children}
    </span>
  );
}; 

