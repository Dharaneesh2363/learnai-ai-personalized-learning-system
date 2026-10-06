export type UserRole = 'student' | 'teacher' | 'admin';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Course {
  id: number;
  title: string;
  slug: string;
  description: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  thumbnail_url: string;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface Resource {
  id: number;
  lesson_id: number;
  title: string;
  resource_type: string;
  url?: string;
  content?: string;
}

export interface Lesson {
  id: number;
  topic_id: number;
  title: string;
  slug: string;
  content_markdown: string;
  order_index: number;
  duration_minutes: number;
  is_published: boolean;
  resources?: Resource[];
}

export interface TopicPrerequisite {
  prerequisite_topic_id: number;
  prerequisite_title?: string;
}

export interface Topic {
  id: number;
  module_id: number;
  title: string;
  slug: string;
  description: string;
  order_index: number;
  estimated_minutes: number;
  lessons?: Lesson[];
  prerequisites?: TopicPrerequisite[];
}

export interface Module {
  id: number;
  course_id: number;
  title: string;
  description: string;
  order_index: number;
  topics: Topic[];
}

export interface CourseDetail extends Course {
  modules: Module[];
}

export interface QuestionOption {
  id: string;
  text: string;
}

export interface QuestionClient {
  id: number;
  topic_id: number;
  question_text: string;
  difficulty: 'easy' | 'medium' | 'hard';
  question_type: 'multiple_choice' | 'true_false' | 'code_snippet';
  options_json: QuestionOption[];
  points: number;
  concept_tag?: string;
}

export interface QuizSummary {
  id: number;
  course_id: number;
  topic_id?: number;
  title: string;
  description: string;
  time_limit_minutes: number;
  passing_score: number;
  is_adaptive: boolean;
  question_count: number;
  created_at: string;
}

export interface QuizTake {
  id: number;
  course_id: number;
  topic_id?: number;
  title: string;
  description: string;
  time_limit_minutes: number;
  passing_score: number;
  is_adaptive: boolean;
  questions: QuestionClient[];
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  user_id: number;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  is_completed: boolean;
  current_difficulty: 'easy' | 'medium' | 'hard';
  started_at: string;
  completed_at?: string;
}

export interface AnswerResult {
  question_id: number;
  question_text: string;
  selected_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
  points_awarded: number;
  time_spent_seconds: number;
}

export interface QuizAttemptDetail extends QuizAttempt {
  quiz_title: string;
  answers: AnswerResult[];
  mastery_changes: Array<{
    topic_id: number;
    topic_title: string;
    mastery_score: number;
    level: string;
    trend: string;
    confidence: number;
  }>;
}

export interface AdaptiveStepResponse {
  is_correct: boolean;
  explanation: string;
  correct_answer: string;
  current_difficulty: 'easy' | 'medium' | 'hard';
  next_question?: QuestionClient;
  is_completed: boolean;
  questions_answered: number;
  total_questions: number;
}

export interface TopicMastery {
  id: number;
  user_id: number;
  topic_id: number;
  topic_title: string;
  module_title: string;
  course_title: string;
  course_id?: number;
  mastery_score: number;
  confidence: number;
  attempts_count: number;
  correct_answers: number;
  incorrect_answers: number;
  last_practiced_at: string;
  trend: 'improving' | 'stable' | 'declining';
  current_difficulty: 'easy' | 'medium' | 'hard';
  weak_concepts: string[];
  strong_concepts: string[];
  level: 'beginner' | 'developing' | 'proficient' | 'mastered';
  updated_at: string;
}

export interface MasterySummary {
  overall_mastery: number;
  total_topics: number;
  mastered_count: number;
  proficient_count: number;
  developing_count: number;
  beginner_count: number;
  top_weak_topics: TopicMastery[];
  top_strong_topics: TopicMastery[];
  topics: TopicMastery[];
}

export interface Recommendation {
  id: number;
  user_id: number;
  topic_id?: number;
  lesson_id?: number;
  topic_title?: string;
  course_id?: number;
  course_title?: string;
  title: string;
  what_description: string;
  why_description: string;
  evidence_description: string;
  action_description: string;
  priority: 'high' | 'medium' | 'low';
  recommendation_type: 'revision' | 'practice_quiz' | 'next_topic' | 'challenge';
  difficulty: 'easy' | 'medium' | 'hard';
  estimated_duration_minutes: number;
  is_completed: boolean;
  is_dismissed: boolean;
  created_at: string;
}

export interface StudyPlanItem {
  id: number;
  study_plan_id: number;
  topic_id?: number;
  lesson_id?: number;
  topic_title?: string;
  course_title?: string;
  day_of_week: number;
  title: string;
  description?: string;
  estimated_minutes: number;
  is_completed: boolean;
  completed_at?: string;
}

export interface StudyPlan {
  id: number;
  user_id: number;
  title: string;
  plan_type: 'daily' | 'weekly';
  start_date: string;
  end_date: string;
  target_hours: number;
  is_active: boolean;
  items: StudyPlanItem[];
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata_json: {
    hints?: string[];
    follow_up_questions?: string[];
    [key: string]: any;
  };
  created_at: string;
}

export interface ChatSession {
  id: number;
  user_id: number;
  topic_id?: number;
  course_id?: number;
  topic_title?: string;
  course_title?: string;
  title: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ChatSessionSummary {
  id: number;
  topic_id?: number;
  title: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface DashboardAnalytics {
  overall_mastery: number;
  quizzes_taken: number;
  average_quiz_score: number;
  learning_streak_days: number;
  total_time_spent_minutes: number;
  topics_in_progress: number;
  topics_mastered: number;
  mastery_by_topic: Array<{
    topic_id: number;
    topic_title: string;
    mastery_score: number;
    level: string;
    current_difficulty: string;
  }>;
  quiz_trend: Array<{
    attempt_id: number;
    quiz_title: string;
    percentage: number;
    date: string;
  }>;
  recent_activity: Array<{
    date: string;
    event_count: number;
  }>;
  top_weak_concepts: string[];
  top_strong_concepts: string[];
}
