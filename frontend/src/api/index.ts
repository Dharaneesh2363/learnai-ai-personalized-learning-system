import { api } from './client';
import * as T from './types';

export const authApi = {
  login: async (email: string, password: string): Promise<T.AuthResponse> => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (email: string, password: string, full_name: string): Promise<T.AuthResponse> => {
    const res = await api.post('/auth/register', { email, password, full_name });
    return res.data;
  },
  getMe: async (): Promise<T.User> => {
    const res = await api.get('/auth/me');
    return res.data;
  },
  logout: async () => {
    await api.post('/auth/logout');
  },
};

export const coursesApi = {
  getCourses: async (category?: string): Promise<T.Course[]> => {
    const res = await api.get('/courses', { params: { category } });
    return res.data;
  },
  getCourseDetail: async (id: number): Promise<T.CourseDetail> => {
    const res = await api.get(`/courses/${id}`);
    return res.data;
  },
  getTopicDetail: async (id: number): Promise<T.Topic> => {
    const res = await api.get(`/courses/topics/${id}`);
    return res.data;
  },
  getLessonDetail: async (id: number): Promise<T.Lesson> => {
    const res = await api.get(`/courses/lessons/${id}`);
    return res.data;
  },
};

export const quizzesApi = {
  getQuizzes: async (params?: { course_id?: number; topic_id?: number }): Promise<T.QuizSummary[]> => {
    const res = await api.get('/quizzes', { params });
    return res.data;
  },
  getQuizTake: async (quizId: number): Promise<T.QuizTake> => {
    const res = await api.get(`/quizzes/${quizId}/take`);
    return res.data;
  },
  startAttempt: async (quizId: number): Promise<T.QuizAttempt> => {
    const res = await api.post(`/quizzes/${quizId}/start-attempt`);
    return res.data;
  },
  submitAdaptiveStep: async (data: {
    attempt_id: number;
    question_id: number;
    selected_answer: string;
    time_spent_seconds: number;
  }): Promise<T.AdaptiveStepResponse> => {
    const res = await api.post('/quizzes/adaptive-step', data);
    return res.data;
  },
  submitStandardQuiz: async (
    quizId: number,
    answers: Array<{ question_id: number; selected_answer: string; time_spent_seconds: number }>
  ): Promise<T.QuizAttempt> => {
    const res = await api.post(`/quizzes/${quizId}/submit`, { answers });
    return res.data;
  },
  getAttemptDetail: async (attemptId: number): Promise<T.QuizAttemptDetail> => {
    const res = await api.get(`/quizzes/attempts/${attemptId}`);
    return res.data;
  },
};

export const masteryApi = {
  getSummary: async (): Promise<T.MasterySummary> => {
    const res = await api.get('/mastery/summary');
    return res.data;
  },
  getTopics: async (): Promise<T.TopicMastery[]> => {
    const res = await api.get('/mastery/topics');
    return res.data;
  },
};

export const recommendationsApi = {
  getRecommendations: async (refresh: boolean = false): Promise<T.Recommendation[]> => {
    const res = await api.get('/recommendations', { params: { refresh } });
    return res.data;
  },
  getHero: async (): Promise<T.Recommendation | null> => {
    const res = await api.get('/recommendations/hero');
    return res.data;
  },
  actOnRecommendation: async (id: number, feedback: { is_completed?: boolean; is_dismissed?: boolean }): Promise<T.Recommendation> => {
    const res = await api.post(`/recommendations/${id}/action`, feedback);
    return res.data;
  },
};

export const studyPlansApi = {
  getCurrent: async (): Promise<T.StudyPlan> => {
    const res = await api.get('/study-plans/current');
    return res.data;
  },
  toggleItem: async (itemId: number): Promise<T.StudyPlanItem> => {
    const res = await api.post(`/study-plans/items/${itemId}/toggle`);
    return res.data;
  },
  regenerate: async (): Promise<T.StudyPlan> => {
    const res = await api.post('/study-plans/generate');
    return res.data;
  },
};

export const tutorApi = {
  getSessions: async (): Promise<T.ChatSessionSummary[]> => {
    const res = await api.get('/tutor/sessions');
    return res.data;
  },
  createSession: async (data: { topic_id?: number; course_id?: number; title?: string }): Promise<T.ChatSession> => {
    const res = await api.post('/tutor/sessions', null, { params: data });
    return res.data;
  },
  getSessionDetail: async (id: number): Promise<T.ChatSession> => {
    const res = await api.get(`/tutor/sessions/${id}`);
    return res.data;
  },
  askTutor: async (data: { session_id?: number; topic_id?: number; course_id?: number; message: string }) => {
    const res = await api.post('/tutor/ask', data);
    return res.data;
  },
};

export const analyticsApi = {
  getDashboard: async (): Promise<T.DashboardAnalytics> => {
    const res = await api.get('/analytics/dashboard');
    return res.data;
  },
  getAdmin: async () => {
    const res = await api.get('/analytics/admin');
    return res.data;
  },
};

export const adminApi = {
  getStudents: async () => {
    const res = await api.get('/admin/students');
    return res.data;
  },
  getQuestions: async (topicId?: number) => {
    const res = await api.get('/admin/questions', { params: { topic_id: topicId } });
    return res.data;
  },
  generateAIQuestions: async (data: { topic_id: number; difficulty: string; count: number; weak_concepts: string[] }) => {
    const res = await api.post('/admin/generate-ai-questions', data);
    return res.data;
  },
};
