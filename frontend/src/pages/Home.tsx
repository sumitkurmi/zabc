// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// Home page rendering complaint registration form and modal email-OTP verification step.

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getConfig, requestOTP, verifyOTP, resendOTP } from '../api/complaints';
import { ConfigResponse, ProblemType } from '../types';
import { ComplaintForm } from '../components/form/ComplaintForm';
import { ChatLauncher } from '../components/chat/ChatLauncher';
import { ChatPanel } from '../components/chat/ChatPanel';
import { Shield, KeyRound, ArrowLeft, RefreshCw, AlertCircle ,LifeBuoy } from 'lucide-react';
import logo from '../assets/logo.jpeg'

export const Home: React.FC = () => {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [aiFilledData, setAiFilledData] = useState<{
    problem_type: ProblemType;
    additional_comment: string;
  } | undefined>(undefined);
  const [hasAutoFilled, setHasAutoFilled] = useState(false);

  // OTP Verification State
  const [otpStep, setOtpStep] = useState<boolean>(false);
  const [pendingId, setPendingId] = useState<string>('');
  const [submittedEmail, setSubmittedEmail] = useState<string>('');
  const [otpCode, setOtpCode] = useState<string>('');
  const [cooldown, setCooldown] = useState<number>(60);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [otpError, setOtpError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    // getConfig().then((data) => setConfig(data));
    getConfig().then((data: ConfigResponse) => setConfig(data));
  }, []);

  // Cooldown countdown timer
  useEffect(() => {
    let timer: any = null;
    if (otpStep && cooldown > 0) {
      timer = setInterval(() => setCooldown((prev) => prev - 1), 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [otpStep, cooldown]);

  const handleFormSubmit = async (formData: any) => {
    setIsSubmitting(true);
    setOtpError(null);
    try {
      const chatId = sessionStorage.getItem('student_chat_id') || undefined;
      const payload = {
        ...formData,
        chat_id: chatId,
        filled_by_ai: hasAutoFilled
      };

      const res = await requestOTP(payload);
      setPendingId(res.pending_id);
      setSubmittedEmail(formData.email);
      setCooldown(res.resend_cooldown_seconds || 60);
      setOtpStep(true);
    } catch (err: any) {
      alert(err.message || 'OTP request failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode || otpCode.length !== 6) {
      setOtpError('Please enter 6-digit OTP');
      return;
    }

    setVerifying(true);
    setOtpError(null);
    try {
      const res = await verifyOTP(pendingId, otpCode);
      navigate(`/success/${res.ticket_id}`);
    } catch (err: any) {
      setOtpError(err.message || 'OTP verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const handleResendOTP = async () => {
    if (cooldown > 0) return;
    setVerifying(true);
    setOtpError(null);
    try {
      const res = await resendOTP(pendingId);
      setCooldown(res.resend_cooldown_seconds || 60);
      setOtpError(null);
      alert('A fresh OTP code has been sent to your email.');
    } catch (err: any) {
      setOtpError(err.message || 'Failed to resend OTP');
    } finally {
      setVerifying(false);
    }
  };

  const handleAutoFillForm = (data: { problem_type: ProblemType; additional_comment: string }) => {
    setAiFilledData(data);
    setHasAutoFilled(true);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* College Header */}
      {/* <header className="bg-mnnit-blue text-white shadow-lg sticky top-0 z-30">
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
              href="/login"
              className="text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-1 transition-colors"
            >
              <Shield className="w-3.5 h-3.5 text-mnnit-gold" />
              <span>Staff Login</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Student Form or OTP Verification Modal Step */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-8 w-full">
        {otpStep ? (
          <div className="bg-white rounded-3xl shadow-xl border border-slate-200 max-w-md mx-auto p-8 my-8">
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <KeyRound className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">Verify Email OTP</h2>
              <p className="text-xs text-slate-500 mt-1">
                A 6-digit code was sent to <span className="font-semibold text-slate-800">{submittedEmail}</span>
              </p>
            </div>

            {otpError && (
              <div className="p-3 bg-red-50 text-red-700 text-xs flex items-center gap-2 rounded-xl mb-4 border border-red-100">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{otpError}</span>
              </div>
            )}

            <form onSubmit={handleVerifyOTP} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Enter 6-Digit OTP</label>
                <input
                  type="text"
                  maxLength={6}
                  autoComplete="one-time-code"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="e.g. 123456"
                  required
                  className="w-full text-center tracking-widest text-lg font-bold font-mono py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <button
                type="submit"
                disabled={verifying || otpCode.length !== 6}
                className="w-full py-3 bg-mnnit-blue hover:bg-blue-800 text-white font-semibold rounded-xl shadow-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {verifying ? 'Verifying OTP...' : 'Verify & Register Complaint'}
              </button>

              <div className="flex items-center justify-between text-xs pt-2">
                <button
                  type="button"
                  onClick={() => setOtpStep(false)}
                  className="text-slate-500 hover:text-slate-700 flex items-center gap-1"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Change Email</span>
                </button>

                <button
                  type="button"
                  disabled={cooldown > 0 || verifying}
                  onClick={handleResendOTP}
                  className="text-blue-600 hover:text-blue-800 font-semibold disabled:text-slate-400 flex items-center gap-1"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>{cooldown > 0 ? `Resend OTP (${cooldown}s)` : 'Resend OTP'}</span>
                </button>
              </div>
            </form>
          </div>
        ) : config ? (
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
