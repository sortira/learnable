import { z } from "zod";

export const workspaceSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  description: z.string().nullable().default(null),
  created_at: z.string(),
  updated_at: z.string()
});

export const documentSchema = z.object({
  id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  source_id: z.string().uuid(),
  title: z.string(),
  content_markdown: z.string(),
  structure_json: z.record(z.unknown()),
  created_at: z.string()
});

export const sourceSchema = z.object({
  id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  kind: z.enum(["upload", "url", "text"]),
  title: z.string(),
  status: z.enum(["queued", "processing", "ready", "failed"]),
  mime_type: z.string().nullable().default(null),
  uri: z.string().nullable().default(null),
  original_filename: z.string().nullable().default(null),
  created_at: z.string(),
  updated_at: z.string()
});

export const chunkSchema = z.object({
  id: z.string().uuid(),
  document_id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  text: z.string(),
  section: z.string().nullable().default(null),
  citation: z.string().nullable().default(null),
  score: z.number().optional()
});

export const searchResultSchema = z.object({
  chunk_id: z.string().uuid(),
  document_id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  text: z.string(),
  citation: z.string().nullable().default(null),
  score: z.number()
});

export const searchResponseSchema = z.object({
  query: z.string(),
  results: z.array(searchResultSchema)
});

export const runNodeSchema = z.object({
  id: z.string().uuid(),
  research_run_id: z.string().uuid(),
  node_type: z.string(),
  title: z.string(),
  status: z.string(),
  payload_json: z.record(z.unknown()),
  created_at: z.string()
});

export const evidenceCardSchema = z.object({
  id: z.string().uuid(),
  research_run_id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  claim: z.string(),
  summary: z.string(),
  supporting_chunk_ids: z.array(z.string().uuid()),
  confidence: z.number().min(0).max(1),
  citations: z.array(z.string()),
  created_at: z.string()
});

export const researchRunSchema = z.object({
  id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  query: z.string(),
  status: z.enum(["queued", "running", "completed", "failed", "cancelled"]),
  summary: z.string().nullable().default(null),
  report_markdown: z.string().nullable().default(null),
  plan_json: z.record(z.unknown()).default({}),
  metrics_json: z.record(z.unknown()).default({}),
  created_at: z.string(),
  updated_at: z.string()
});

export const reportSchema = z.object({
  run: researchRunSchema,
  nodes: z.array(runNodeSchema),
  evidence_cards: z.array(evidenceCardSchema)
});

export const flashcardSchema = z.object({
  id: z.string().uuid(),
  front: z.string(),
  back: z.string(),
  concept: z.string()
});

export const flashcardDeckSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  created_at: z.string(),
  cards: z.array(flashcardSchema)
});

export const quizQuestionSchema = z.object({
  id: z.string().uuid(),
  prompt: z.string(),
  answer: z.string(),
  difficulty: z.enum(["easy", "medium", "hard"]),
  concept: z.string()
});

export const quizSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  created_at: z.string(),
  questions: z.array(quizQuestionSchema)
});

export const studyPlanSchema = z.object({
  id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  title: z.string(),
  schedule_markdown: z.string(),
  created_at: z.string()
});

export const masteryStateSchema = z.object({
  concept: z.string(),
  mastery_score: z.number(),
  attempts_count: z.number().int(),
  updated_at: z.string()
});

export type Workspace = z.infer<typeof workspaceSchema>;
export type Document = z.infer<typeof documentSchema>;
export type Source = z.infer<typeof sourceSchema>;
export type Chunk = z.infer<typeof chunkSchema>;
export type SearchResult = z.infer<typeof searchResultSchema>;
export type SearchResponse = z.infer<typeof searchResponseSchema>;
export type RunNode = z.infer<typeof runNodeSchema>;
export type EvidenceCard = z.infer<typeof evidenceCardSchema>;
export type ResearchRun = z.infer<typeof researchRunSchema>;
export type Report = z.infer<typeof reportSchema>;
export type Flashcard = z.infer<typeof flashcardSchema>;
export type FlashcardDeck = z.infer<typeof flashcardDeckSchema>;
export type QuizQuestion = z.infer<typeof quizQuestionSchema>;
export type Quiz = z.infer<typeof quizSchema>;
export type StudyPlan = z.infer<typeof studyPlanSchema>;
export type MasteryState = z.infer<typeof masteryStateSchema>;
