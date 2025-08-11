import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs/promises";

export async function GET(req: NextRequest) {
  // Try to find the backend digest file robustly
  // __dirname is not available, so use import.meta.url to get the current file location
  const here = path.dirname(new URL(import.meta.url).pathname);
  // Traverse up to the project root, then to backend/app/agent
  const projectRoot = path.resolve(here, '../../../../..');
  const backendDir = path.join(projectRoot, 'backend/app/agent');
  try {
    const files = await fs.readdir(backendDir);
    const digests = files.filter(f => f.startsWith('digest-') && f.endsWith('.md'));
    if (digests.length === 0) {
      return new NextResponse('No digest file found. Please run the backend script first.', { status: 404 });
    }
    digests.sort().reverse();
    const latest = digests[0];
    const content = await fs.readFile(path.join(backendDir, latest), 'utf-8');
    return new NextResponse(content, { status: 200 });
  } catch (e) {
    return new NextResponse('Error reading digest: ' + (e instanceof Error ? e.message : 'Unknown error'), { status: 500 });
  }
}
