import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getCategoryDetail, uploadDocument, deleteDocument, unassignChatFromReference, previewDocument, getAdminChatDetail, } from '../../api/admin';
import { CategoryDetailResponse } from '../../types';
import { UploadDropzone } from '../../components/admin/UploadDropzone';
import { renderAsync } from 'docx-preview';


import {
  Folder,
  ArrowLeft,
  FileText,
  MessageSquare,
  Trash2,
  Download,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertCircle,
  Eye,
} from 'lucide-react';

export const CategoryPage: React.FC = () => {
  const { categoryId } = useParams<{ categoryId: string }>();
  const [data, setData] = useState<CategoryDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'documents' | 'chats'>('documents');
  const [toast, setToast] = useState<string | null>(null);
  const navigate = useNavigate();


  const [previewContent, setPreviewContent] = useState('');
  const [previewFileName, setPreviewFileName] = useState('');
  const [previewType, setPreviewType] = useState<'pdf' | 'docx' | 'text'>('text');
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const [isDocumentPickerOpen, setIsDocumentPickerOpen] = useState(false);
  const [previewMode, setPreviewMode] = useState<'document' | 'chat'>('document');

  const docxPreviewRef = useRef<HTMLDivElement | null>(null);


  useEffect(() => {
    if (
      !isPreviewOpen ||
      isPreviewLoading ||
      previewMode !== 'document' ||
      previewType !== 'docx' ||
      !docxPreviewRef.current ||
      !previewContent
    ) {
      return;
    }

    let cancelled = false;

    const renderDocx = async () => {
      const container = docxPreviewRef.current;
      if (!container) return;

      container.innerHTML = '';

      try {
        const response = await fetch(previewContent);
        if (!response.ok) {
          throw new Error('Unable to read DOCX file');
        }

        const blob = await response.blob();

        if (cancelled) return;

        await renderAsync(blob, container, undefined, {
          inWrapper: true,
          breakPages: true,
        });
      } catch (error) {
        if (!cancelled) {
          container.textContent =
            error instanceof Error
              ? error.message
              : 'Unable to render DOCX preview.';
        }
      }
    };

    void renderDocx();

    return () => {
      cancelled = true;
    };
  }, [
    isPreviewOpen,
    isPreviewLoading,
    previewMode,
    previewType,
    previewContent,
  ]);


  const fetchCategory = () => {
    if (!categoryId) return;
    setIsLoading(true);
    getCategoryDetail(categoryId)
      .then((res) => setData(res))
      .catch((err) => {
        if (err.message && err.message.includes('401')) {
          navigate('/admin/login');
        }
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchCategory();
  }, [categoryId]);

  const handleUploadFile = async (file: File) => {
    if (!categoryId) return;
    setIsUploading(true);
    try {
      const doc = await uploadDocument(categoryId, file);
      setToast(`Uploaded "${file.name}". Processing and vector indexing started.`);
      fetchCategory();
      setTimeout(() => setToast(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDoc = async (docId: string, filename: string) => {
    if (!window.confirm(`Delete document "${filename}" and purge vector embeddings?`)) return;
    try {
      await deleteDocument(docId);
      setToast(`Document "${filename}" deleted.`);
      fetchCategory();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to delete document');
    }
  };



  const handlePreview = async (docId: string, fileName: string) => {
    setPreviewMode('document');
    setPreviewFileName(fileName);
    setPreviewContent('');
    setPreviewType('text');
    setIsPreviewOpen(true);
    setIsPreviewLoading(true);

    try {
      const result = await previewDocument(docId);
      setPreviewContent(result.content);
      setPreviewType(result.type);
    } catch (error) {
      setPreviewContent(
        `Unable to preview file: ${error instanceof Error ? error.message : 'Something went wrong'
        }`
      );
      setPreviewType('text');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleChatPreview = async (chatId: string, chatPreview: string) => {
    setPreviewMode('chat');
    setPreviewFileName('Chat Transcript');
    setPreviewContent('');
    setPreviewType('text');
    setIsPreviewOpen(true);
    setIsPreviewLoading(true);

    try {
      const result = await getAdminChatDetail(chatId);

      const transcript = result.messages
        .map((message) => {
          const role = message.role === 'user' ? 'Student' : 'Assistant';
          return `${role}:\n${message.content}`;
        })
        .join('\n\n');

      setPreviewContent(transcript || chatPreview || 'No messages found.');
    } catch (error) {
      setPreviewContent(
        `Unable to load chat transcript: ${error instanceof Error ? error.message : 'Something went wrong'
        }`
      );
    } finally {
      setIsPreviewLoading(false);
    }
  };



  const handleRemoveChat = async (chatId: string) => {
    if (!window.confirm('Remove chat from reference category?')) return;
    try {
      await unassignChatFromReference(chatId);
      setToast('Chat removed from reference category.');
      fetchCategory();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to remove chat');
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin/reference" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">{data?.category.name || 'Category Detail'}</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {toast && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-semibold flex items-center gap-2 shadow-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{toast}</span>
          </div>
        )}

        {isLoading ? (
          <div className="p-12 text-center text-slate-400">Loading category detail...</div>
        ) : !data ? (
          <div className="p-12 text-center text-slate-500">Category not found.</div>
        ) : (
          <div>
            {/* Category Banner */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-mnnit-blue flex items-center justify-center">
                  <Folder className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-800">{data.category.name}</h2>
                  <p className="text-xs text-slate-500">{data.category.description}</p>
                </div>
              </div>
            </div>

            {/* Document Drag & Drop Uploadzone */}
            <UploadDropzone onUpload={handleUploadFile} isUploading={isUploading} />

            {/* Tabs for Documents and Chats */}
            <div className="flex border-b border-slate-200 mb-6">
              <button
                onClick={() => setActiveTab('documents')}
                className={`pb-3 px-4 font-semibold text-xs flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'documents'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
              >
                <FileText className="w-4 h-4" />
                <span>Documents ({data.documents.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('chats')}
                className={`pb-3 px-4 font-semibold text-xs flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'chats'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
              >
                <MessageSquare className="w-4 h-4" />
                <span>Promoted Chats ({data.chats.length})</span>
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'documents' ? (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                {data.documents.length === 0 ? (
                  <div className="p-12 text-center text-slate-400 text-sm">No uploaded documents in this category.</div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {data.documents.map((doc) => (
                      <div key={doc.id} className="p-4 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-semibold text-slate-800 truncate">{doc.original_filename}</p>
                              {doc.source_type === 'COMPLAINT' && (
                                <span className="text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded-full shrink-0">
                                  From complaint
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                              <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                              <span>•</span>
                              <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                              <span>•</span>
                              <span>{doc.chunk_count} chunks indexed</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          {/* Status Badge */}
                          {doc.status === 'INDEXED' && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3" /> INDEXED
                            </span>
                          )}
                          {doc.status === 'PROCESSING' && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                              <Clock className="w-3 h-3 animate-spin" /> PROCESSING
                            </span>
                          )}
                          {doc.status === 'FAILED' && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-red-700 bg-red-50 px-2.5 py-1 rounded-full border border-red-200" title={doc.error_message || ''}>
                              <AlertCircle className="w-3 h-3" /> FAILED
                            </span>
                          )}




                          {/* View document */}
                          {(doc.source_type === 'UPLOAD' || doc.source_type === 'COMPLAINT') &&
                            /\.(pdf|txt|docx)$/i.test(doc.original_filename) && (
                              <button
                                type="button"
                                onClick={() => handlePreview(doc.id, doc.original_filename)}
                                className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-slate-50"
                                title="View document"
                                aria-label={`View ${doc.original_filename}`}
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                            )}




                          {/* Download original */}
                          {doc.source_type === 'UPLOAD' && (
                            <a
                              href={`/api/admin/documents/${doc.id}/download`}
                              download
                              className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-slate-50"
                              title="Download original file"
                            >
                              <Download className="w-4 h-4" />
                            </a>
                          )}

                          {/* Delete document */}
                          <button
                            onClick={() => handleDeleteDoc(doc.id, doc.original_filename)}
                            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                            title="Delete document and purge vectors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                {data.chats.length === 0 ? (
                  <div className="p-12 text-center text-slate-400 text-sm">No chats promoted to this category yet.</div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {data.chats.map((chat) => (
                      <div key={chat.id} className="p-4 flex items-center justify-between gap-4">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-slate-800 truncate">{chat.preview}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{chat.message_count} messages • #{chat.id.slice(-6)}</p>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleChatPreview(chat.id, chat.preview)}
                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleRemoveChat(chat.id)}
                            className="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 rounded-lg text-xs font-semibold flex items-center gap-1"
                          >
                            <RotateCcw className="w-3.5 h-3.5" /> Remove from Reference
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>


      {/* Document Preview Modal */}

      {isPreviewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <div className="flex min-w-0 items-center gap-2">
                <FileText className="h-5 w-5 shrink-0 text-blue-600" />
                <h2 className="truncate text-base font-semibold text-slate-800">
                  {previewFileName}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => {
                  if (previewType === 'pdf' && previewContent.startsWith('blob:')) {
                    URL.revokeObjectURL(previewContent);
                  }
                  setIsPreviewOpen(false);
                }}
                className="ml-4 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800"
              >
                Close
              </button>
            </div>


            <div className="min-h-0 flex-1 overflow-auto p-5">
              {isPreviewLoading ? (
                <p className="py-8 text-center text-sm text-slate-500">
                  Loading preview...
                </p>
              ) :  previewMode === 'document' && previewType === 'docx' ? (
              <div
                ref={docxPreviewRef}
                className="docx-preview-container min-w-0"
              />
              ) : previewMode === 'document' && previewType === 'pdf' ? (
              <iframe
                src={previewContent}
                title={previewFileName}
                className="h-[70vh] w-full rounded-lg border border-slate-200"
              />
              ) : (
              <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-6 text-slate-700">
                {previewContent}
              </pre>
)}
            </div>

          </div>
        </div>
      )}


    </div>
  );
};
