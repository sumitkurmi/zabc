import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getConfig, submitComplaint } from '../api/complaints';
import { ConfigResponse, ProblemType } from '../types';
import { ComplaintForm } from '../components/form/ComplaintForm';
import { ChatLauncher } from '../components/chat/ChatLauncher';
import { ChatPanel } from '../components/chat/ChatPanel';
import { Shield, LifeBuoy } from 'lucide-react';

export const Home: React.FC = () => {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [aiFilledData, setAiFilledData] = useState<{
    problem_type: ProblemType;
    additional_comment: string;
  } | undefined>(undefined);
  const [hasAutoFilled, setHasAutoFilled] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    getConfig().then((data) => setConfig(data));
  }, []);

  const handleFormSubmit = async (formData: any) => {
    setIsSubmitting(true);
    try {
      const chatId = sessionStorage.getItem('student_chat_id') || undefined;
      const res = await submitComplaint({
        ...formData,
        chat_id: chatId,
        filled_by_ai: hasAutoFilled
      });
      navigate(`/success/${res.ref_no}`);
    } catch (err: any) {
      alert(err.message || 'Submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAutoFillForm = (data: { problem_type: ProblemType; additional_comment: string }) => {
    setAiFilledData(data);
    setHasAutoFilled(true);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* College Header */}
      <header className="bg-mnnit-blue text-white shadow-lg sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center font-bold text-mnnit-gold border border-white/20 text-sm">
              MNNIT
            </div>
            <div>
              <h1 className="text-base sm:text-lg font-bold tracking-tight">
                {config?.college_name || 'MNNIT Allahabad'}
              </h1>
              <p className="text-[11px] text-slate-200">Network Complaint & AI Diagnosis Portal</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="/admin/login"
              className="text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-1 transition-colors"
            >
              <Shield className="w-3.5 h-3.5 text-mnnit-gold" />
              <span>Admin Login</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Student Form */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-8 w-full">
        {config ? (
          <ComplaintForm
            locations={config.locations}
            problemTypes={config.problem_types}
            onSubmit={handleFormSubmit}
            isSubmitting={isSubmitting}
            autoFilled={hasAutoFilled}
            aiFilledData={aiFilledData}
          />
        ) : (
          <div className="p-12 text-center text-slate-400">Loading portal configuration...</div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} MNNIT Allahabad IT Services. All Rights Reserved.
      </footer>

      {/* Floating Chat Launcher & Side Panel */}
      <ChatLauncher onClick={() => setIsChatOpen(true)} isOpen={isChatOpen} />
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onAutoFillForm={handleAutoFillForm}
        hasAutoFilled={hasAutoFilled}
      />
    </div>
  );
};
