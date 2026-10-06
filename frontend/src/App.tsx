import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Courses } from './pages/Courses';
import { CourseDetail } from './pages/CourseDetail';
import { LessonView } from './pages/LessonView';
import { Quizzes } from './pages/Quizzes';
import { AdaptiveQuizTaker } from './pages/AdaptiveQuizTaker';
import { QuizResult } from './pages/QuizResult';
import { Recommendations } from './pages/Recommendations';
import { StudyPlan } from './pages/StudyPlan';
import { AITutor } from './pages/AITutor';
import { Analytics } from './pages/Analytics';
import { Profile } from './pages/Profile';
import { AdminDashboard } from './pages/Admin/AdminDashboard';
import { AdminStudents } from './pages/Admin/AdminStudents';
import { AdminQuestions } from './pages/Admin/AdminQuestions';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user || (user.role !== 'admin' && user.role !== 'teacher')) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Student / Teacher Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="courses" element={<Courses />} />
              <Route path="courses/:id" element={<CourseDetail />} />
              <Route path="learn/:lessonId" element={<LessonView />} />
              <Route path="quizzes" element={<Quizzes />} />
              <Route path="quiz/:attemptId" element={<AdaptiveQuizTaker />} />
              <Route path="results/:attemptId" element={<QuizResult />} />
              <Route path="recommendations" element={<Recommendations />} />
              <Route path="study-plan" element={<StudyPlan />} />
              <Route path="tutor" element={<AITutor />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="profile" element={<Profile />} />

              {/* Admin Routes */}
              <Route
                path="admin"
                element={
                  <AdminRoute>
                    <AdminDashboard />
                  </AdminRoute>
                }
              />
              <Route
                path="admin/students"
                element={
                  <AdminRoute>
                    <AdminStudents />
                  </AdminRoute>
                }
              />
              <Route
                path="admin/questions"
                element={
                  <AdminRoute>
                    <AdminQuestions />
                  </AdminRoute>
                }
              />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
