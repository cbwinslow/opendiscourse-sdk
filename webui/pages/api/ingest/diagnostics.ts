import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }
  try {
    const apiRes = await fetch(
      process.env.BACKEND_URL + "/ingest/diagnostics",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req.body),
      }
    );
    const data = await apiRes.json();
    res.status(apiRes.status).json(data);
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
}
