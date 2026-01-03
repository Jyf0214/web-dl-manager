import { NextRequest, NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';
import { processDownloadJob } from '@/lib/tasks';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const url = formData.get('url') as string;
    const upload_service = formData.get('upload_service') as string;

    if (!url || !upload_service) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    const taskId = uuidv4();
    const params: Record<string, any> = {};
    formData.forEach((value, key) => {
      params[key] = value;
    });

    // Start background task
    // Note: In Next.js App Router, background tasks can be tricky if the function returns early.
    // For a robust implementation, consider an external task queue (like BullMQ or simply a background process).
    // Here we'll start it and not await it.
    processDownloadJob(taskId, url, params).catch(console.error);

    return NextResponse.json({ 
      status: 'success', 
      task_id: taskId,
      message: 'Download task started' 
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
