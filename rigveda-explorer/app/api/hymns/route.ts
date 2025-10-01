import { NextResponse } from 'next/server';
import { GetAllHymns } from '@/lib/db';

export async function GET() {
  try {
    const hymns = GetAllHymns();
    return NextResponse.json(hymns);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch hymns' }, { status: 500 });
  }
}


