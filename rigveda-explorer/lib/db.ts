import Database from 'better-sqlite3';
import path from 'path';

const dbPath = path.join(process.cwd(), 'hymn_vectors.db');
const db = new Database(dbPath, { readonly: true });

export interface Hymn {
  hymn_id: string;
  book_number: number;
  hymn_number: number;
  title: string;
  deity_vector: string;
  deity_names: string;
  deity_count: number;
  hymn_score: number;
}

export interface Deity {
  deity_name: string;
  deity_frequency: number;
}

export function GetAllHymns(): Hymn[] {
  const stmt = db.prepare('SELECT * FROM hymn_vectors ORDER BY hymn_score DESC');
  return stmt.all() as Hymn[];
}

export function GetHymnById(hymnId: string): Hymn | undefined {
  const stmt = db.prepare('SELECT * FROM hymn_vectors WHERE hymn_id = ?');
  return stmt.get(hymnId) as Hymn | undefined;
}

export function GetSimilarHymns(hymnId: string, limit: number = 8): Hymn[] {
  const hymn = GetHymnById(hymnId);
  if (!hymn) return [];
  
  const vector = JSON.parse(hymn.deity_vector);
  const allHymns = GetAllHymns();
  
  const similarities = allHymns
    .filter(h => h.hymn_id !== hymnId)
    .map(h => {
      const otherVector = JSON.parse(h.deity_vector);
      const similarity = CosineSimilarity(vector, otherVector);
      return { hymn: h, similarity };
    })
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit);
  
  return similarities.map(s => s.hymn);
}

function CosineSimilarity(v1: number[], v2: number[]): number {
  const dotProduct = v1.reduce((sum, val, i) => sum + val * v2[i], 0);
  const mag1 = Math.sqrt(v1.reduce((sum, val) => sum + val * val, 0));
  const mag2 = Math.sqrt(v2.reduce((sum, val) => sum + val * val, 0));
  
  if (mag1 === 0 || mag2 === 0) return 0;
  return dotProduct / (mag1 * mag2);
}

export function GetDeityInfo(): Deity[] {
  const stmt = db.prepare('SELECT deity_name, deity_frequency FROM deity_index ORDER BY deity_frequency DESC');
  return stmt.all() as Deity[];
}


