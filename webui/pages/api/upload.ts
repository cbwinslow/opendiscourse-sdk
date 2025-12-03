import type { NextApiRequest, NextApiResponse } from "next";
import formidable from "formidable";
import fs from "fs";
import path from "path";

export const config = {
  api: { bodyParser: false },
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }
  
  const form = formidable({
    uploadDir: '/tmp',
    keepExtensions: true,
    maxFileSize: 50 * 1024 * 1024, // 50MB
  });
  
  form.parse(req, async (err, fields, files) => {
    if (err) {
      console.error('Form parsing error:', err);
      res.status(500).json({ error: "Failed to parse form" });
      return;
    }
    
    const file = Array.isArray(files.file) ? files.file[0] : files.file;
    if (!file) {
      res.status(400).json({ error: "No file uploaded" });
      return;
    }
    
    try {
      // Verify the file path is within /tmp to prevent path traversal
      const TMP_ROOT = "/tmp";
      const absFilePath = fs.realpathSync(path.resolve(TMP_ROOT, path.basename(file.filepath)));
      if (!absFilePath.startsWith(TMP_ROOT)) {
        res.status(400).json({ error: "Invalid file path" });
        return;
      }
      // Create form data for backend API
      const formData = new FormData();
      const fileBuffer = fs.readFileSync(absFilePath);
      const blob = new Blob([fileBuffer], { type: file.mimetype || 'application/octet-stream' });
      formData.append('file', blob, file.originalFilename || 'uploaded-file');
      
      const apiRes = await fetch(process.env.BACKEND_URL + "/api/v1/documents/upload", {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${process.env.API_TOKEN || ""}`,
        },
        body: formData,
      });
      
      const data = await apiRes.json();
      
      // Clean up temp file
      fs.unlinkSync(absFilePath);
      
      res.status(apiRes.status).json(data);
    } catch (e: any) {
      console.error('Upload error:', e);
      res.status(500).json({ error: e.message });
    }
  });
}
