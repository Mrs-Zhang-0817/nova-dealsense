import {Slot} from "@radix-ui/react-slot";
import {cva} from "class-variance-authority";
import {cn} from "@/lib/utils";
const buttonVariants = cva("rounded-md border px-4 py-2 text-sm font-medium focus-visible:outline-2 hover:brightness-125");
export function Button({asChild, className, ...props}: React.ComponentProps<"button"> & {asChild?:boolean}) {
  const Component = asChild ? Slot : "button";
  return <Component className={cn(buttonVariants(), className)} {...props}/>;
}
