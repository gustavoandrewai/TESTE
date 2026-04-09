import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/dashboard", "/recipients", "/newsletters", "/settings"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const protectedPath = PROTECTED.some((p) => pathname === p || pathname.startsWith(`${p}/`));
  const token = request.cookies.get("admin_session")?.value;

  if (protectedPath && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (pathname === "/login" && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/recipients/:path*", "/newsletters/:path*", "/settings/:path*", "/login"]
};
