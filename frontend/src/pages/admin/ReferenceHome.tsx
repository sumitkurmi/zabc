import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getReferenceCategories } from '../../api/admin';
import { CategorySummary } from '../../types';
import { BookOpen, Folder, ArrowLeft, FileText, MessageSquare } from 'lucide-react';

export const ReferenceHome: React.FC = () => {
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getReferenceCategories()
      .then((data) => setCategories(data))
      .catch((err) => {
        if (err.message && err.message.includes('401')) {
          navigate('/admin/login');
        }
      })
      .finally(() => setIsLoading(false));
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">Reference Categories Knowledge Base</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-800">Reference Categories</h2>
          <p className="text-xs text-slate-500 mt-1">
            Curated categories holding promoted chats and official SOP documents used by RAG chatbot.
          </p>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-slate-400">Loading categories...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((cat) => (
              <Link
                key={cat.slug}
                to={`/admin/reference/${cat.slug}`}
                className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 hover:shadow-lg hover:border-blue-300 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-mnnit-blue flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <Folder className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-slate-800 mb-1">{cat.name}</h3>
                  <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{cat.description}</p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600 font-medium">
                  <span className="flex items-center gap-1">
                    <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
                    {cat.chats_count} chats
                  </span>
                  <span className="flex items-center gap-1">
                    <FileText className="w-3.5 h-3.5 text-emerald-600" />
                    {cat.documents_count} docs
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};
