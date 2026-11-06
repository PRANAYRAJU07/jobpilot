import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    try {
        const res = await fetch("http://jobpilot_backend:8000/api/applications/debug");
        if (!res.ok) {
            return NextResponse.json({ error: "Backend error" }, { status: res.status });
        }
        const data = await res.json();
        return NextResponse.json(data);
    } catch (e) {
        return NextResponse.json({ error: "Failed to connect to backend" }, { status: 500 });
    }
}
