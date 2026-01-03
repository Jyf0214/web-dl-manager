import { NextResponse } from 'next/server';
import { getAllTasks } from '@/lib/status';

export async function GET() {
  try {
    const tasks = await getAllTasks();
    return NextResponse.json(tasks);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
