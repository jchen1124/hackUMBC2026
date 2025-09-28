import React from "react";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "success" | "warning";
  size?: "sm" | "default" | "lg" | "xl" | "icon";
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className = "",
    variant = "default",
    size = "default",
    children,
    disabled = false,
    loading = false,
    ...props
  }, ref) => {
    const baseStyles = "inline-flex items-center justify-center rounded-md font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";

    const variants = {
      default: "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 shadow-sm hover:shadow-md",
      destructive: "bg-red-600 text-white hover:bg-red-700 active:bg-red-800 shadow-sm hover:shadow-md",
      outline: "border border-gray-300 bg-white text-gray-900 hover:bg-gray-50 hover:border-gray-400 active:bg-gray-100 shadow-sm",
      secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200 active:bg-gray-300 shadow-sm",
      ghost: "text-gray-700 hover:bg-gray-100 hover:text-gray-900 active:bg-gray-200",
      link: "text-blue-600 underline-offset-4 hover:underline hover:text-blue-700 active:text-blue-800",
      success: "bg-green-600 text-white hover:bg-green-700 active:bg-green-800 shadow-sm hover:shadow-md",
      warning: "bg-yellow-500 text-white hover:bg-yellow-600 active:bg-yellow-700 shadow-sm hover:shadow-md"
    };

    const sizes = {
      sm: "h-8 px-3 text-sm gap-1",
      default: "h-10 px-4 py-2 gap-2",
      lg: "h-12 px-6 text-lg gap-2",
      xl: "h-14 px-8 text-xl gap-3",
      icon: "h-10 w-10"
    };

    const buttonStyles = `${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`;

    return (
      <button
        ref={ref}
        className={buttonStyles}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button };
