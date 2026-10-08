import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const alertVariants = cva(
  cn(
    "group/alert relative grid w-full grid-cols-[0_1fr] items-start gap-y-1 rounded border-2 px-4 py-3 text-left text-sm shadow-md",
    "has-[>svg]:grid-cols-[1.25rem_1fr] has-[>svg]:gap-x-3",
    "has-data-[slot=alert-action]:pr-14",
    "[&>svg]:size-5 [&>svg]:translate-y-0.5 [&>svg]:shrink-0 [&>svg]:text-current"
  ),
  {
    variants: {
      variant: {
        default:
          "border-border bg-background text-foreground *:data-[slot=alert-description]:text-muted-foreground",
        destructive:
          "border-border bg-[#ebcfc9] text-foreground *:data-[slot=alert-description]:text-foreground/80",
        solid:
          "border-border bg-foreground text-background *:data-[slot=alert-description]:text-background/80",
      },
      status: {
        error:
          "border-border bg-[#ebcfc9] text-foreground *:data-[slot=alert-description]:text-foreground/80",
        success:
          "border-border bg-[#cfe1d3] text-foreground *:data-[slot=alert-description]:text-foreground/80",
        warning:
          "border-border bg-[#efdf9f] text-foreground *:data-[slot=alert-description]:text-foreground/80",
        info: "border-border bg-[#d6e2ec] text-foreground *:data-[slot=alert-description]:text-foreground/80",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Alert({
  className,
  variant,
  status,
  ...props
}: React.ComponentProps<"div"> & VariantProps<typeof alertVariants>) {
  return (
    <div
      data-slot="alert"
      role="alert"
      className={cn(alertVariants({ variant, status }), className)}
      {...props}
    />
  )
}

function AlertTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="alert-title"
      className={cn(
        "col-start-2 min-h-5 font-head text-base leading-tight tracking-tight [&_a]:underline [&_a]:underline-offset-3",
        className
      )}
      {...props}
    />
  )
}

function AlertDescription({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="alert-description"
      className={cn(
        "col-start-2 grid justify-items-start gap-1 text-sm [&_a]:underline [&_a]:underline-offset-3 [&_a]:hover:text-foreground [&_p]:leading-relaxed [&_p:not(:last-child)]:mb-4",
        className
      )}
      {...props}
    />
  )
}

function AlertAction({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="alert-action"
      className={cn("absolute top-2 right-2", className)}
      {...props}
    />
  )
}

export { Alert, AlertTitle, AlertDescription, AlertAction, alertVariants }
