import React, { useState } from 'react';
import { LocationOption, ProblemType, ProblemTypeOption } from '../../types';
import { Sparkles, Send, CheckCircle, AlertCircle } from 'lucide-react';

interface ComplaintFormProps {
  locations: LocationOption[];
  problemTypes: ProblemTypeOption[];
  onSubmit: (formData: any) => Promise<void>;
  isSubmitting: boolean;
  autoFilled: boolean;
  aiFilledData?: { problem_type: ProblemType; additional_comment: string };
}

export const ComplaintForm: React.FC<ComplaintFormProps> = ({
  locations,
  problemTypes,
  onSubmit,
  isSubmitting,
  autoFilled,
  aiFilledData
}) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    mobile: '',
    location: locations[0]?.id || 'hostel_a',
    address_room: '',
    preferred_from: '09:00',
    preferred_to: '17:00',
    problem_type: problemTypes[0]?.value || ('WIFI_PROBLEM' as ProblemType),
    additional_comment: '',
    honeypot: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Sync AI pre-fill data if passed
  React.useEffect(() => {
    if (aiFilledData) {
      setFormData((prev) => ({
        ...prev,
        problem_type: aiFilledData.problem_type,
        additional_comment: aiFilledData.additional_comment
      }));
      setToastMessage('Filled by AI. Please review before submitting.');
      setTimeout(() => setToastMessage(null), 5000);
    }
  }, [aiFilledData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear error on change
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim() || formData.name.length < 2 || formData.name.length > 80) {
      newErrors.name = 'Name must be between 2 and 80 characters';
    }

    if (!formData.email.trim() || !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Valid email address required';
    }

    if (!formData.mobile.trim() || !/^(\+91)?\d{10}$/.test(formData.mobile)) {
      newErrors.mobile = 'Enter 10-digit mobile number';
    }

    if (!formData.address_room.trim() || formData.address_room.length > 100) {
      newErrors.address_room = 'Address/Room No required (max 100 chars)';
    }

    if (!formData.preferred_from) {
      newErrors.preferred_from = 'Start time required';
    }

    if (!formData.preferred_to) {
      newErrors.preferred_to = 'End time required';
    } else if (formData.preferred_from && formData.preferred_to <= formData.preferred_from) {
      newErrors.preferred_to = 'End time must be later than start time';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit(formData);
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden max-w-2xl mx-auto my-6">
      {/* Form Header */}
      <div className="bg-mnnit-blue text-white p-6">
        <h1 className="text-xl font-bold">Network Complaint Registration</h1>
        <p className="text-xs text-slate-200 mt-1">
          MNNIT Allahabad IT Services Support Portal
        </p>
      </div>

      {/* AI Pre-fill Toast Banner */}
      {toastMessage && (
        <div className="bg-emerald-50 border-b border-emerald-200 p-4 text-xs text-emerald-800 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-mnnit-gold shrink-0 animate-pulse" />
          <span className="font-semibold">{toastMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="p-6 space-y-5">
        {/* Honeypot field */}
        <input
          type="text"
          name="honeypot"
          value={formData.honeypot}
          onChange={handleChange}
          className="hidden"
          tabIndex={-1}
          autoComplete="off"
        />

        {/* Student Name & Email */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g. Rahul Sharma"
              className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 ${
                errors.name ? 'border-red-500 focus:ring-red-300' : 'border-slate-300 focus:ring-blue-600'
              }`}
            />
            {errors.name && <p className="text-[11px] text-red-500 mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Email Address <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="e.g. student@mnnit.ac.in"
              className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 ${
                errors.email ? 'border-red-500 focus:ring-red-300' : 'border-slate-300 focus:ring-blue-600'
              }`}
            />
            {errors.email && <p className="text-[11px] text-red-500 mt-1">{errors.email}</p>}
          </div>
        </div>

        {/* Mobile & Location */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Mobile Number <span className="text-red-500">*</span>
            </label>
            <input
              type="tel"
              name="mobile"
              value={formData.mobile}
              onChange={handleChange}
              placeholder="10-digit mobile number"
              className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 ${
                errors.mobile ? 'border-red-500 focus:ring-red-300' : 'border-slate-300 focus:ring-blue-600'
              }`}
            />
            {errors.mobile && <p className="text-[11px] text-red-500 mt-1">{errors.mobile}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Location / Area <span className="text-red-500">*</span>
            </label>
            <select
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="w-full p-2.5 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
            >
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Room / Address */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Address / Room No. <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="address_room"
            value={formData.address_room}
            onChange={handleChange}
            placeholder="e.g. Room 214, Block B"
            className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 ${
              errors.address_room ? 'border-red-500 focus:ring-red-300' : 'border-slate-300 focus:ring-blue-600'
            }`}
          />
          {errors.address_room && <p className="text-[11px] text-red-500 mt-1">{errors.address_room}</p>}
        </div>

        {/* Preferred Time Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Preferred Time From <span className="text-red-500">*</span>
            </label>
            <input
              type="time"
              name="preferred_from"
              value={formData.preferred_from}
              onChange={handleChange}
              className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 ${
                errors.preferred_from ? 'border-red-500 focus:ring-red-300' : 'border-slate-300 focus:ring-blue-600'
              }`}
            />
            {errors.preferred_from && <p className="text-[11px] text-red-500 mt-1">{errors.preferred_from}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Preferred Time To <span className="text-red-500">*</span>
            </label>
            <input
              type="time"
              name="preferred_to"
              value={formData.preferred_to}
              onChange={handleChange}
              className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 ${
                errors.preferred_to ? 'border-red-500 focus:ring-red-300' : 'border-slate-300 focus:ring-blue-600'
              }`}
            />
            {errors.preferred_to && <p className="text-[11px] text-red-500 mt-1">{errors.preferred_to}</p>}
          </div>
        </div>

        {/* Problem Type Select */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-700">
              Problem Type <span className="text-red-500">*</span>
            </label>
            {autoFilled && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                <Sparkles className="w-3 h-3 text-mnnit-gold" /> AI Pre-filled
              </span>
            )}
          </div>
          <select
            name="problem_type"
            value={formData.problem_type}
            onChange={handleChange}
            className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-white ${
              autoFilled ? 'border-emerald-400 bg-emerald-50/20' : 'border-slate-300 focus:ring-blue-600'
            }`}
          >
            {problemTypes.map((pt) => (
              <option key={pt.value} value={pt.value}>
                {pt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Additional Comment */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-slate-700">
              Additional Comment (Optional)
            </label>
            {autoFilled && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                <Sparkles className="w-3 h-3 text-mnnit-gold" /> AI Pre-filled
              </span>
            )}
          </div>
          <textarea
            name="additional_comment"
            value={formData.additional_comment}
            onChange={handleChange}
            rows={4}
            maxLength={1000}
            placeholder="Describe your issue or steps tried..."
            className={`w-full p-2.5 text-sm border rounded-xl focus:outline-none focus:ring-2 ${
              autoFilled ? 'border-emerald-400 bg-emerald-50/20' : 'border-slate-300 focus:ring-blue-600'
            }`}
          />
          <div className="flex justify-between text-[11px] text-slate-400 mt-1">
            <span>Provide device details or error messages</span>
            <span>{formData.additional_comment.length}/1000</span>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 bg-mnnit-blue hover:bg-blue-800 text-white font-semibold rounded-xl shadow-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isSubmitting ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Submit Network Complaint</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
