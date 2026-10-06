import React, { useEffect, useState } from 'react';
import { adminApi } from '../../api';
import { Badge } from '../../components/Badge';
import { Users, Award, HelpCircle, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export const AdminStudents: React.FC = () => {
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const data = await adminApi.getStudents();
        setStudents(data);
      } catch (err) {
        console.error('Failed to load students:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStudents();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        to="/admin"
        className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition font-medium"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Admin Hub
      </Link>

      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Users className="w-6 h-6 text-purple-400" /> Student Cohort Roster
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Detailed cognitive analytics and assessment activity for all registered learners.
        </p>
      </div>

      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase font-mono tracking-wider">
              <tr>
                <th className="p-4">Student</th>
                <th className="p-4">Email</th>
                <th className="p-4">Average Mastery</th>
                <th className="p-4">Quizzes Taken</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 font-semibold text-white flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-indigo-400">
                      {student.full_name.charAt(0)}
                    </div>
                    <span>{student.full_name}</span>
                  </td>
                  <td className="p-4 text-slate-400 font-mono">{student.email}</td>
                  <td className="p-4">
                    <span className="font-mono font-bold text-indigo-400 text-sm">
                      {student.average_mastery}%
                    </span>
                  </td>
                  <td className="p-4 font-mono text-slate-300">
                    {student.quizzes_attempted} attempts
                  </td>
                  <td className="p-4">
                    <Badge variant={student.is_active ? 'emerald' : 'rose'}>
                      {student.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
