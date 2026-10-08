/** The team album: the host's surprise for a team after the game (requirements §1, R-10). One chapter per
 *  landmark the team reached, with the photos it took there, the riddle it solved and the landmark's story.
 *  Design draft: these types describe what the album API will return; the preview renders mock data. */

export interface AlbumPhoto {
  url: string;
  taken_at: string;            // ISO-8601, UTC; shown in the game's time zone
}

export interface AlbumChapter {
  number: number;              // 1-based task number
  landmark: string;
  story: string;               // the landmark's tourist info, paragraphs separated by blank lines
  reached_at: string;          // when the team solved the riddle (ISO-8601, UTC)
  photos: AlbumPhoto[];
}

export interface Album {
  game: string;
  team: string;
  time_zone: string;
  played_on: string;           // the start of the run (ISO-8601, UTC)
  task_count: number;
  total_seconds: number | null;   // null when the run ended unfinished
  rank: number | null;
  shared_rank: boolean;
  host_message: string;
  chapters: AlbumChapter[];
}
