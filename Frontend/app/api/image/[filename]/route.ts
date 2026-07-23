import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const runtime = "nodejs";

const ASSETS_DIR = path.resolve(process.env.ASSETS_DIR || "uploads/screenshots");

export async function GET(
  req: Request,
  context: { params: Promise<{ filename: string }> }
) {
  const { filename } = await context.params;

  if (!filename) {
    return new NextResponse("Filename missing", { status: 400 });
  }

  const filePath = path.join(ASSETS_DIR, filename);

  if (!fs.existsSync(filePath)) {
    return new NextResponse("File not found", { status: 404 });
  }

  const fileBuffer = fs.readFileSync(filePath);

  return new NextResponse(fileBuffer, {
    headers: {
      "Content-Type": "image/png",
    },
  });
}
