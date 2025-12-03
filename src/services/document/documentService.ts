import { query, getClient } from '../../config/database';
import { QueryResult } from 'pg';

export interface Document {
    id: string;
    title: string;
    content?: string;
    content_vector?: number[];
    file_path?: string;
    mime_type?: string;
    file_size?: number;
    folder_id?: string;
    created_by: string;
    version: number;
    metadata: Record<string, any>;
}

export class DocumentService {
    async createDocument(doc: Partial<Document>): Promise<Document> {
        const client = await getClient();
        try {
            await client.query('BEGIN');

            // Insert document
            const documentResult = await client.query(
                `INSERT INTO documents 
                (title, content, file_path, mime_type, file_size, folder_id, created_by, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *`,
                [
                    doc.title,
                    doc.content,
                    doc.file_path,
                    doc.mime_type,
                    doc.file_size,
                    doc.folder_id,
                    doc.created_by,
                    doc.metadata || {}
                ]
            );

            // Create initial version
            await client.query(
                `INSERT INTO document_versions 
                (document_id, version_number, content, file_path, file_size, created_by, metadata)
                VALUES ($1, 1, $2, $3, $4, $5, $6)`,
                [
                    documentResult.rows[0].id,
                    doc.content,
                    doc.file_path,
                    doc.file_size,
                    doc.created_by,
                    doc.metadata || {}
                ]
            );

            await client.query('COMMIT');
            return documentResult.rows[0];
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    async getDocument(id: string, userId: string): Promise<Document | null> {
        // Log access
        await this.logAccess(id, userId, 'read');

        const result = await query(
            `SELECT d.*, 
                    array_agg(DISTINCT t.name) as tags,
                    p.permission_level
             FROM documents d
             LEFT JOIN document_tags dt ON d.id = dt.document_id
             LEFT JOIN tags t ON dt.tag_id = t.id
             LEFT JOIN permissions p ON d.id = p.resource_id 
                AND p.resource_type = 'document' 
                AND p.user_id = $2
             WHERE d.id = $1 AND NOT d.is_deleted
             GROUP BY d.id, p.permission_level`,
            [id, userId]
        );

        return result.rows[0] || null;
    }

    async updateDocument(id: string, doc: Partial<Document>, userId: string): Promise<Document> {
        const client = await getClient();
        try {
            await client.query('BEGIN');

            // Get current version
            const versionResult = await client.query(
                'SELECT version FROM documents WHERE id = $1',
                [id]
            );
            const newVersion = versionResult.rows[0].version + 1;

            // Update document
            const updateResult = await client.query(
                `UPDATE documents 
                SET title = COALESCE($1, title),
                    content = COALESCE($2, content),
                    file_path = COALESCE($3, file_path),
                    mime_type = COALESCE($4, mime_type),
                    file_size = COALESCE($5, file_size),
                    folder_id = COALESCE($6, folder_id),
                    version = $7,
                    metadata = COALESCE($8, metadata)
                WHERE id = $9 AND NOT is_deleted
                RETURNING *`,
                [
                    doc.title,
                    doc.content,
                    doc.file_path,
                    doc.mime_type,
                    doc.file_size,
                    doc.folder_id,
                    newVersion,
                    doc.metadata,
                    id
                ]
            );

            // Create new version
            await client.query(
                `INSERT INTO document_versions 
                (document_id, version_number, content, file_path, file_size, created_by, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)`,
                [
                    id,
                    newVersion,
                    doc.content,
                    doc.file_path,
                    doc.file_size,
                    userId,
                    doc.metadata
                ]
            );

            await client.query('COMMIT');
            return updateResult.rows[0];
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    async deleteDocument(id: string, userId: string): Promise<void> {
        await query(
            'UPDATE documents SET is_deleted = true WHERE id = $1',
            [id]
        );
        await this.logAccess(id, userId, 'delete');
    }

    async searchDocuments(
        query: string,
        folderId?: string,
        tags?: string[],
        userId?: string,
        limit: number = 10,
        offset: number = 0
    ): Promise<{ documents: Document[], total: number }> {
        const whereConditions = ['NOT d.is_deleted'];
        const params: any[] = [];
        let paramCounter = 1;

        if (query) {
            whereConditions.push(`(
                d.title ILIKE $${paramCounter} OR
                d.content ILIKE $${paramCounter} OR
                EXISTS (
                    SELECT 1 FROM tags t
                    JOIN document_tags dt ON t.id = dt.tag_id
                    WHERE dt.document_id = d.id AND t.name ILIKE $${paramCounter}
                )
            )`);
            params.push(`%${query}%`);
            paramCounter++;
        }

        if (folderId) {
            whereConditions.push(`d.folder_id = $${paramCounter}`);
            params.push(folderId);
            paramCounter++;
        }

        if (tags && tags.length > 0) {
            const tagPlaceholders = tags.map((_, idx) => `$${paramCounter + idx}`).join(',');
            whereConditions.push(`EXISTS (
                SELECT 1 FROM document_tags dt
                JOIN tags t ON dt.tag_id = t.id
                WHERE dt.document_id = d.id AND t.name IN (${tagPlaceholders})
            )`);
            params.push(...tags);
            paramCounter += tags.length;
        }

        if (userId) {
            whereConditions.push(`(
                d.created_by = $${paramCounter} OR
                EXISTS (
                    SELECT 1 FROM permissions p
                    WHERE p.resource_type = 'document'
                    AND p.resource_id = d.id
                    AND p.user_id = $${paramCounter}
                )
            )`);
            params.push(userId);
            paramCounter++;
        }

        const whereClause = whereConditions.length > 0 
            ? 'WHERE ' + whereConditions.join(' AND ')
            : '';

        // Get total count
        const countResult = await query(
            `SELECT COUNT(DISTINCT d.id) as total
             FROM documents d
             ${whereClause}`,
            params
        );

        // Get documents
        params.push(limit, offset);
        const result = await query(
            `SELECT d.*, 
                    array_agg(DISTINCT t.name) as tags
             FROM documents d
             LEFT JOIN document_tags dt ON d.id = dt.document_id
             LEFT JOIN tags t ON dt.tag_id = t.id
             ${whereClause}
             GROUP BY d.id
             ORDER BY d.updated_at DESC
             LIMIT $${paramCounter} OFFSET $${paramCounter + 1}`,
            params
        );

        return {
            documents: result.rows,
            total: parseInt(countResult.rows[0].total)
        };
    }

    private async logAccess(documentId: string, userId: string, accessType: string): Promise<void> {
        await query(
            `INSERT INTO document_access_log 
            (document_id, user_id, access_type, ip_address)
            VALUES ($1, $2, $3, $4)`,
            [documentId, userId, accessType, '127.0.0.1'] // IP address should come from request
        );
    }
}
