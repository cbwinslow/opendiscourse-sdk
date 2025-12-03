import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }
  
  try {
    const { question, context, documentIds } = req.body;
    
    const apiRes = await fetch(process.env.BACKEND_URL + "/api/v1/rag/query", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.API_TOKEN || ""}`,
      },
      body: JSON.stringify({
        question,
        context,
        document_ids: documentIds,
        max_results: 5,
      }),
    });
    
    if (!apiRes.ok) {
      throw new Error(`Backend API error: ${apiRes.status}`);
    }
    
    const data = await apiRes.json();
    res.status(200).json(data);
  } catch (e: any) {
    console.error('Query error:', e);
    res.status(500).json({ error: e.message });
  }
}
