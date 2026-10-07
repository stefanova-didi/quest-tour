export interface Coordinates {
  lat: number;
  lon: number;
}

export interface Landmark {
  id: number;
  key: string;
  name: string;
  task: string;
  accepted_answers: string[];
  hint1: string | null;
  hint2: string | null;
  tourist_info: string;
  coordinates: Coordinates | null;
  task_image_url: string | null;
  info_image_url: string | null;
  updated_at: string;
}

export interface RevealSettings {
  attempts: number;
  minutes: number;
  penalty_minutes: number;
}

export interface Game {
  id: number;
  key: string;
  name: string;
  intro: string;
  time_zone: string;
  max_duration_minutes: number;
  reveal: RevealSettings;
  updated_at: string;
  task_landmark_ids: number[];
}

export interface Team {
  id: number;
  key: string;
  name: string;
  participants: number | null;
  updated_at: string;
}

export interface AssignmentCreate {
  game_id: number;
  valid_from: string;
  valid_until: string;
  exit_message: string;
}

export interface AssignmentOut {
  id: number;
  game_id: number;
  game_name: string;
  valid_from: string;
  valid_until: string;
  exit_message: string;
  token_issued: boolean;
  issued_at: string | null;
  updated_at: string;
}

export interface TokenReveal {
  assignment_id: number;
  token: string;
  url: string;
}

export interface TeamPhotoOut {
  id: number;
  team_name: string;
  game_name: string;
  uploaded_at: string;
  url: string;
}

export interface ConflictBody {
  entity: string;
  current: { id: number; updated_at: string };
}

export type LandmarkInput = Omit<Landmark, "id" | "updated_at" | "task_image_url" | "info_image_url">;
export type GameInput = Omit<Game, "id" | "updated_at" | "task_landmark_ids">;
export type TeamInput = Omit<Team, "id" | "updated_at">;
