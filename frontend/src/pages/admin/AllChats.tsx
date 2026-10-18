import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAdminChats, deleteChat, moveChatToReference } from '../../api/admin';
import { ChatSummary, ProblemType } from '../../types';
import {
  MessageSquare,
  Search,
  ChevronLeft,
  ChevronRight,
  FolderInput,
  Trash2,
  X,
  CheckCircle2,
  ArrowLeft
} from 'lucide-react';

const CATEGORY_SLUGS = [
  { slug: 'complaint-logs', name: 'Complaint & Fault Logs' },
  { slug: 'admin-observations', name: 'Admin Observations' },
  { slug: 'corrective-measures', name: 'Approved Corrective Measures' },
  { slug: 'frequent-problems', name: 'Frequently Encountered Problems' },
  { slug: 'student-guidelines', name: 'Student Troubleshooting Guidelines' },
  { slug: 'manuals-sops', name: 'Device Manuals & SOPs' }
];

export const AllChats: React.FC = () => {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [q, setQ] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  // Move dialog state
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [selectedCategorySlug, setSelectedCategorySlug] = useState<string>(CATEGORY_SLUGS[0].slug);
  const [toast, setToast] = useState<string | null>(null);

  const navigate = useNavigate();

  const fetchChats = () => {
    setIsLoading(true);
    getAdminChats('UNASSIGNED', page, q, categoryFilter)
      .then((data) => {
        setChats(data.chats);
        setTotal(data.total);
        setPages(data.pages);
      })
      .catch((err) => {
        if (err.message && err.message.includes('401')) {
          navigate('/admin/login');
        }
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchChats();
  }, [page, categoryFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchChats();
  };

  const handleConfirmMove = async () => {
    if (!selectedChatId) return;
    try {
      await moveChatToReference(selectedChatId, selectedCategorySlug);
      setToast('Chat moved to reference category & queued for indexing');
      setSelectedChatId(null);
      fetchChats();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to move chat');
    }
  };

  const handleDelete = async (chatId: string) => {
    if (!window.confirm('Are you sure you want to delete this chat transcript?')) return;
    try {
      await deleteChat(chatId);
      setToast('Chat deleted successfully');
      fetchChats();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to delete chat');
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">Unassigned Student Chats</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Toast alert */}
        {toast && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-semibold flex items-center gap-2 shadow-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{toast}</span>
          </div>
        )}

        {/* Filter & Search Bar */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <form onSubmit={handleSearchSubmit} className="flex-1 w-full flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search chat transcript text..."
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-mnnit-blue hover:bg-blue-800 text-white rounded-xl text-xs font-semibold transition-colors shrink-0"
            >
              Search
            </button>
          </form>

          <div className="w-full sm:w-auto flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500 shrink-0">Category:</span>
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              className="p-2 text-xs border border-slate-300 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="">All Categories</option>
              <option value="WIFI_PROBLEM">WIFI PROBLEM</option>
              <option value="LAN_PROBLEM">LAN PROBLEM</option>
              <option value="IP_ADDRESS_ISSUE">I.P ADDRESS ISSUE</option>
              <option value="PROXY_ISSUE">PROXY ISSUE</option>
              <option value="LAN_PORT_BROKEN">LAN PORT BROKEN</option>
            </select>
          </div>
        </div>

        {/* Chat List Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-sm">Loading conversations...</div>
          ) : chats.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-sm">No unassigned chats found.</div>
          ) : (
            <div className="divide-y divide-slate-100">
              {chats.map((chat) => (
                <div key={chat.id} className="p-4 hover:bg-slate-50/80 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-slate-400">#{chat.id.slice(-6)}</span>
                      {chat.detected_category ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                          {chat.detected_category.replace(/_/g, ' ')}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-500">
                          Unclassified
                        </span>
                      )}
                      <span className="text-[11px] text-slate-400">
                        {new Date(chat.created_at).toLocaleString()}
                      </span>
                    </div>

                    <p className="text-sm text-slate-800 font-medium truncate">{chat.preview}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{chat.message_count} user messages</p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link
                      to={`/admin/chats/${chat.id}`}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => setSelectedChatId(chat.id)}
                      className="px-3 py-1.5 bg-mnnit-blue hover:bg-blue-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
                    >
                      <FolderInput className="w-3.5 h-3.5" />
                      Move to Ref
                    </button>
                    <button
                      onClick={() => handleDelete(chat.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete chat"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {chats.length} of {total} chats</span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-1 border rounded-lg disabled:opacity-30 hover:bg-white"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span>Page {page} of {pages}</span>
              <button
                disabled={page >= pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-1 border rounded-lg disabled:opacity-30 hover:bg-white"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Move to Reference Modal Dialog */}
      {selectedChatId && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-800">Move Chat to Reference</h3>
              <button onClick={() => setSelectedChatId(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Select one of six reference categories. The transcript will be indexed in ChromaDB for future student chatbot retrieval.
            </p>

            <div className="space-y-2 mb-6">
              {CATEGORY_SLUGS.map((cat) => (
                <label
                  key={cat.slug}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                    selectedCategorySlug === cat.slug
                      ? 'border-blue-600 bg-blue-50/50 font-semibold text-blue-900'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="category"
                    value={cat.slug}
                    checked={selectedCategorySlug === cat.slug}
                    onChange={(e) => setSelectedCategorySlug(e.target.value)}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-xs">{cat.name}</span>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setSelectedChatId(null)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmMove}
                className="px-4 py-2 bg-mnnit-blue hover:bg-blue-800 text-white rounded-xl text-xs font-semibold"
              >
                Confirm & Index
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
