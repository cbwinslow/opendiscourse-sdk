import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }
  try {
    const apiRes = await fetch(
      process.env.BACKEND_URL + "/diagnostics/linux"
    );
    const data = await apiRes.json();
    res.status(apiRes.status).json(data);
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
}
