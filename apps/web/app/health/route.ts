export function GET() {
  const commit = (process.env.RELEASE_SHA ?? "").trim().slice(0, 12) || "unknown";
  return Response.json({ status: "ok", service: "web", commit }, { headers: { "Cache-Control": "no-store" } });
}
