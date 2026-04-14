"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Plus, X, Eye, Save, Loader2, Library, Sparkles, Globe,
} from "lucide-react";
import MovieCard, { MovieCardSkeleton } from "@/components/MovieCard";
import { collectionsAPI, genresAPI } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import type { MovieCompact, Genre, CollectionRule } from "@/types/movie";

const FIELD_OPTIONS: { value: string; label: string; type: "select" | "number" | "text" }[] = [
  { value: "genre", label: "Genre", type: "select" },
  { value: "year_min", label: "Year (from)", type: "number" },
  { value: "year_max", label: "Year (to)", type: "number" },
  { value: "rating_min", label: "Rating (min)", type: "number" },
  { value: "rating_max", label: "Rating (max)", type: "number" },
  { value: "runtime_min", label: "Runtime min (min)", type: "number" },
  { value: "runtime_max", label: "Runtime max (min)", type: "number" },
  { value: "language", label: "Language", type: "text" },
  { value: "sort_by", label: "Sort by", type: "select" },
];

const SORT_OPTIONS = [
  { value: "popularity.desc", label: "Most Popular" },
  { value: "vote_average.desc", label: "Highest Rated" },
  { value: "primary_release_date.desc", label: "Newest First" },
  { value: "primary_release_date.asc", label: "Oldest First" },
  { value: "revenue.desc", label: "Highest Revenue" },
];

export default function NewCollectionPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [rules, setRules] = useState<Omit<CollectionRule, "id">[]>([]);
  const [genres, setGenres] = useState<Genre[]>([]);

  const [preview, setPreview] = useState<MovieCompact[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewTotal, setPreviewTotal] = useState(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    genresAPI.list().then((data: any) => {
      setGenres(Array.isArray(data) ? data : data.results ?? []);
    }).catch(console.error);
  }, []);

  const loadPreview = useCallback(async () => {
    if (rules.length === 0) {
      setPreview([]);
      setPreviewTotal(0);
      return;
    }
    setPreviewLoading(true);
    try {
      const data = await collectionsAPI.preview(rules);
      setPreview(data.results?.slice(0, 12) || []);
      setPreviewTotal(data.total_results || 0);
    } catch (err) {
      console.error("Preview failed", err);
    } finally {
      setPreviewLoading(false);
    }
  }, [rules]);

  useEffect(() => {
    const timeout = setTimeout(loadPreview, 600);
    return () => clearTimeout(timeout);
  }, [loadPreview]);

  function addRule() {
    setRules((prev) => [...prev, { field: "genre", value: "" }]);
  }

  function updateRule(index: number, key: "field" | "value", val: string) {
    setRules((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [key]: val };
      if (key === "field") next[index].value = "";
      return next;
    });
  }

  function removeRule(index: number) {
    setRules((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSave() {
    if (!name.trim() || rules.length === 0) return;
    setSaving(true);
    try {
      const validRules = rules.filter((r) => r.value.trim() !== "");
      const coverBackdrop = preview[0]
        ? (preview[0] as any).backdrop_path || ""
        : "";
      const col = await collectionsAPI.create({
        name,
        description,
        is_public: isPublic,
        cover_backdrop: coverBackdrop,
        rules: validRules,
      });
      router.push(`/collections/${col.id}`);
    } catch (err) {
      console.error("Failed to save collection", err);
    } finally {
      setSaving(false);
    }
  }

  function renderValueInput(rule: Omit<CollectionRule, "id">, index: number) {
    const fieldDef = FIELD_OPTIONS.find((f) => f.value === rule.field);

    if (rule.field === "genre") {
      return (
        <select
          value={rule.value}
          onChange={(e) => updateRule(index, "value", e.target.value)}
          className="flex-1 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white/80 focus:border-gold/30 focus:outline-none transition-colors"
        >
          <option value="">Select genre…</option>
          {genres.map((g) => (
            <option key={g.tmdb_id} value={String(g.tmdb_id)}>
              {g.name}
            </option>
          ))}
        </select>
      );
    }

    if (rule.field === "sort_by") {
      return (
        <select
          value={rule.value}
          onChange={(e) => updateRule(index, "value", e.target.value)}
          className="flex-1 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white/80 focus:border-gold/30 focus:outline-none transition-colors"
        >
          <option value="">Select sort…</option>
          {SORT_OPTIONS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      );
    }

    return (
      <input
        type={fieldDef?.type === "number" ? "number" : "text"}
        value={rule.value}
        onChange={(e) => updateRule(index, "value", e.target.value)}
        placeholder={
          rule.field === "language" ? "e.g. en, ko, ja" : "Enter value…"
        }
        className="flex-1 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white/80 placeholder:text-white/20 focus:border-gold/30 focus:outline-none transition-colors"
      />
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="pt-32 pb-20 text-center">
        <Library className="w-12 h-12 mx-auto mb-4 text-white/10" />
        <p className="text-white/40 mb-2">Sign in to create collections</p>
      </div>
    );
  }

  return (
    <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1440px] mx-auto">
      {/* Header */}
      <Link
        href="/collections"
        className="inline-flex items-center gap-2 text-sm text-white/30 hover:text-white/60 transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Collections
      </Link>

      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-gold/10 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-gold" />
        </div>
        <div>
          <h1 className="text-3xl font-bold font-display">New Collection</h1>
          <p className="text-sm text-white/30">Define rules and watch your collection come to life</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left: Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
              Collection Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. 90s Sci-Fi Gems"
              className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/20 focus:border-gold/30 focus:outline-none transition-colors"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="What makes this collection special?"
              className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white placeholder:text-white/20 focus:border-gold/30 focus:outline-none transition-colors resize-none"
            />
          </div>

          {/* Public toggle */}
          <label className="flex items-center gap-3 cursor-pointer group">
            <div
              className={`w-10 h-6 rounded-full relative transition-colors ${
                isPublic ? "bg-gold/30" : "bg-white/10"
              }`}
              onClick={() => setIsPublic(!isPublic)}
            >
              <div
                className={`absolute top-1 w-4 h-4 rounded-full transition-all ${
                  isPublic ? "left-5 bg-gold" : "left-1 bg-white/40"
                }`}
              />
            </div>
            <div className="flex items-center gap-2 text-sm text-white/50">
              <Globe className="w-3.5 h-3.5" />
              Make public (shareable)
            </div>
          </label>

          {/* Rules */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold text-white/40 uppercase tracking-wider">
                Filter Rules
              </label>
              <button
                onClick={addRule}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gold/10 text-gold text-xs font-semibold hover:bg-gold/15 transition-colors"
              >
                <Plus className="w-3 h-3" /> Add Rule
              </button>
            </div>

            {rules.length === 0 && (
              <div className="text-center py-8 border border-dashed border-white/[0.08] rounded-xl">
                <p className="text-sm text-white/20">No rules yet. Add filters to define your collection.</p>
              </div>
            )}

            <div className="space-y-3">
              {rules.map((rule, i) => (
                <div key={i} className="flex items-center gap-2">
                  <select
                    value={rule.field}
                    onChange={(e) => updateRule(i, "field", e.target.value)}
                    className="w-40 shrink-0 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white/80 focus:border-gold/30 focus:outline-none transition-colors"
                  >
                    {FIELD_OPTIONS.map((f) => (
                      <option key={f.value} value={f.value}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                  {renderValueInput(rule, i)}
                  <button
                    onClick={() => removeRule(i)}
                    className="w-8 h-8 shrink-0 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center hover:bg-red-500/10 hover:border-red-500/20 transition-colors"
                  >
                    <X className="w-3.5 h-3.5 text-white/40" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Save */}
          <button
            onClick={handleSave}
            disabled={!name.trim() || rules.length === 0 || saving}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-gold to-gold-dim text-surface-0 font-semibold text-sm hover:shadow-lg hover:shadow-gold/15 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saving ? "Saving…" : "Create Collection"}
          </button>
        </div>

        {/* Right: Live Preview */}
        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-gold/60" />
              <h2 className="text-lg font-bold font-display">Live Preview</h2>
            </div>
            {previewTotal > 0 && (
              <span className="text-xs text-white/30">
                {previewTotal.toLocaleString()} movies match
              </span>
            )}
          </div>

          {previewLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <MovieCardSkeleton key={i} />
              ))}
            </div>
          ) : preview.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {preview.map((movie, i) => (
                <MovieCard
                  key={movie.id || movie.tmdb_id}
                  movie={movie}
                  size="sm"
                  index={i}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-20 border border-dashed border-white/[0.06] rounded-xl">
              <Eye className="w-10 h-10 mx-auto mb-3 text-white/10" />
              <p className="text-sm text-white/25">
                Add rules to see matching movies here
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

