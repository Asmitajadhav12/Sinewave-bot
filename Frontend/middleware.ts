import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // ✅ Allow API routes
  if (pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  // ✅ Allow Next.js internal files
  if (pathname.startsWith("/_next")) {
    return NextResponse.next();
  }

  // ✅ Allow static files (images, icons, etc.)
  if (pathname.match(/\.(.*)$/)) {
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|favicon.ico).*)"],
};
