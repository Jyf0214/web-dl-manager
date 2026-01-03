import { NextResponse } from 'next/server';
import { getSystemStatus } from '@/lib/status';

export async function GET() {
  try {
    const status = await getSystemStatus();
    return NextResponse.json(status);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
