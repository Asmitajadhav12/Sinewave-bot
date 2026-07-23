"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

export function Breadcrumb() {
  const pathname = usePathname();

  const pathSegments = pathname
    .split("/")
    .filter((segment) => segment.length > 0);

  return (
    <nav className="flex items-center text-sm text-gray-600 mb-6">
      <Link
        href="/"
        className="hover:text-[#005bac] transition-colors"
      >
        Dashboard
      </Link>

      {pathSegments.map((segment, index) => {
        const href = "/" + pathSegments.slice(0, index + 1).join("/");
        const isLast = index === pathSegments.length - 1;

        return (
          <div key={href} className="flex items-center">
            <ChevronRight className="h-4 w-4 mx-2 text-gray-400" />

            {isLast ? (
              <span className="text-[#005bac] font-medium capitalize">
                {segment}
              </span>
            ) : (
              <Link
                href={href}
                className="hover:text-[#005bac] transition-colors capitalize"
              >
                {segment}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
