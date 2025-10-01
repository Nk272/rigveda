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

export interface HymnDetail {
  hymn: Hymn;
  deities: string[];
  similarHymns: Hymn[];
}

export interface BubbleData {
  hymn: Hymn;
  x: number;
  y: number;
  radius: number;
}


