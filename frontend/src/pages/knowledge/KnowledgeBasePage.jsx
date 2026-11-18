import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { BookOpen, Plus, Search } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { knowledgeService } from "../../services/domainServices";
import { getErrorMessage } from "../../services/api";
import { knowledgeArticleSchema } from "../../validations/schemas";
import { CATEGORIES, formatDateTime, ROLES } from "../../utils/constants";
import { EmptyState, ErrorBanner, LoadingSpinner, Modal, PageHeader } from "../../components/common/UIPrimitives";

export function KnowledgeBasePage() {
  const { user } = useAuth();
  const [articles, setArticles] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [activeArticle, setActiveArticle] = useState(null);

  const canAuthor = [ROLES.ADMIN, ROLES.MANAGER, ROLES.ENGINEER].includes(user?.role);
  const canPublish = [ROLES.ADMIN, ROLES.MANAGER].includes(user?.role);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(knowledgeArticleSchema),
    defaultValues: { category: "OTHER" },
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await knowledgeService.list({
        ...(search ? { search } : {}),
        ...(category ? { category } : {}),
        page_size: 50,
      });
      setArticles(res.results || []);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load knowledge base."));
    } finally {
      setLoading(false);
    }
  }, [search, category]);

  useEffect(() => {
    load();
  }, [load]);

  const onCreate = async (values) => {
    setError("");
    try {
      await knowledgeService.create(values);
      setCreateOpen(false);
      reset();
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to create article."));
    }
  };

  const handlePublish = async (id) => {
    try {
      const updated = await knowledgeService.publish(id);
      setActiveArticle(updated);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to publish article."));
    }
  };

  const handleArchive = async (id) => {
    try {
      const updated = await knowledgeService.archive(id);
      setActiveArticle(updated);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to archive article."));
    }
  };

  return (
    <div>
      <PageHeader
        title="Knowledge Base"
        subtitle="Verified IT troubleshooting guides, runbooks, and self-service resolutions."
        actions={
          canAuthor && (
            <button
              type="button"
              onClick={() => setCreateOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold"
            >
              <Plus className="w-4 h-4" /> New Article
            </button>
          )
        }
      />

      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-5 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search troubleshooting guides..."
            className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white sm:w-56"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError("")} />

      {loading ? (
        <LoadingSpinner />
      ) : articles.length === 0 ? (
        <EmptyState title="No articles found" description="Create a new troubleshooting guide or adjust your search." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {articles.map((art) => (
            <div
              key={art.id}
              onClick={() => knowledgeService.get(art.id).then(setActiveArticle)}
              className="bg-white border border-slate-200 rounded-xl p-5 hover:border-blue-400 cursor-pointer transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-semibold text-blue-700">{art.category}</span>
                  <span className={`px-2 py-0.5 rounded font-semibold ${art.status === "PUBLISHED" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                    {art.status}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 flex items-start gap-2">
                  <BookOpen className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />
                  <span>{art.title}</span>
                </h3>
                <p className="text-xs text-slate-600 mt-2 line-clamp-3">{art.summary}</p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <span>Views: {art.view_count}</span>
                <span>{formatDateTime(art.updated_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={createOpen} title="Create Knowledge Article" onClose={() => setCreateOpen(false)} maxWidth="max-w-2xl">
        <form onSubmit={handleSubmit(onCreate)} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Title</label>
            <input {...register("title")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            {errors.title && <p className="text-xs text-red-600 mt-1">{errors.title.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Category</label>
            <select {...register("category")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Summary</label>
            <textarea rows={2} {...register("summary")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            {errors.summary && <p className="text-xs text-red-600 mt-1">{errors.summary.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Article Content</label>
            <textarea rows={4} {...register("content")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            {errors.content && <p className="text-xs text-red-600 mt-1">{errors.content.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Troubleshooting Steps</label>
            <textarea rows={3} {...register("troubleshooting_steps")} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setCreateOpen(false)} className="px-4 py-2 text-sm rounded-lg border border-slate-300">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="px-4 py-2 text-sm rounded-lg bg-blue-700 text-white font-semibold">Save Draft</button>
          </div>
        </form>
      </Modal>

      <Modal open={!!activeArticle} title={activeArticle?.title || ""} onClose={() => setActiveArticle(null)} maxWidth="max-w-2xl">
        {activeArticle && (
          <div className="space-y-4 text-sm">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Category: <strong>{activeArticle.category}</strong> • Status: <strong>{activeArticle.status}</strong></span>
              <span>Author: {activeArticle.author_detail?.full_name}</span>
            </div>
            <p className="font-medium text-slate-800">{activeArticle.summary}</p>
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 whitespace-pre-wrap text-slate-700">
              {activeArticle.content}
            </div>
            {activeArticle.troubleshooting_steps && (
              <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 whitespace-pre-wrap text-slate-800">
                <div className="text-xs font-bold uppercase text-blue-800 mb-1">Troubleshooting Steps</div>
                {activeArticle.troubleshooting_steps}
              </div>
            )}
            {canPublish && (
              <div className="flex justify-end gap-2 pt-2">
                {activeArticle.status !== "PUBLISHED" && (
                  <button
                    type="button"
                    onClick={() => handlePublish(activeArticle.id)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-700 text-white text-xs font-semibold"
                  >
                    Publish Article
                  </button>
                )}
                {activeArticle.status !== "ARCHIVED" && (
                  <button
                    type="button"
                    onClick={() => handleArchive(activeArticle.id)}
                    className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold"
                  >
                    Archive
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
