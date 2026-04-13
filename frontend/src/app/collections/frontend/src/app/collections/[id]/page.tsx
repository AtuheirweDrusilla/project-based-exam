"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Globe, Lock, Pencil, Trash2, Loader2, Library,
  Share2, Check, Filter,
} from "lucide-react";
import MovieCard, { MovieCardSkeleton } from "@/components/MovieCard";
import { collectionsAPI } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import type { Collection, MovieCompact } from "@/types/movie";

const FIELD_LABELS: Record<string, string> = {
  genre: "Genre",
  year_min: "Year from",
  year_max: "Year to",
  rating_min: "Min rating",
  rating_max: "Max rating",
  runtime_min: "Min runtime",
  runtime_max: "Max runtime",
  language: "Language",
  sort_by: "Sort",
};

export default function CollectionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const id = Number(params.id);

  const [collection, setCollection] = useState<Collection | null>(null);
  const [movies, setMovies] = useState<MovieCompact[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchCollection(1);
  }, [id, isAuthenticated]);

  async function fetchCollection(p: number) {
    setLoading(true);
    try {
      let colData: Collection;
      let movieData: {
        results: MovieCompact[];
        total_pages: number;
        total_results: number;
        page: number;
      };

      if (isAuthenticated) {
        try {
          colData = await collectionsAPI.get(id);
          movieData = await collectionsAPI.getMovies(id, p);
        } catch {
          const pubData = await collectionsAPI.getPublicDetail(id, p);
          colData = pubData.collection;
          movieData = pubData;
        }
      } else {
        const pubData = await collectionsAPI.getPublicDetail(id, p);
        colData = pubData.collection;
        movieData = pubData;
      }

      setCollection(colData);
      setMovies(movieData.results || []);
      setTotalPages(movieData.total_pages || 1);
      setTotalResults(movieData.total_results || 0);
      setPage(p);
    } catch (err) {
      console.error("Failed to load collection", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Permanently delete this collection?")) return;
    try {
      await collectionsAPI.delete(id);
      router.push("/collections");
    } catch (err) {
      console.error("Delete failed", err);
    }
  }

  function handleShare() {
    const url = `${window.location.origin}/collections/${id}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const isOwner = isAuthenticated && user?.username === collection?.owner;

  if (loading && !collection) {
    return (
      <div className="pt-32 flex justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-gold/40" />
      </div>
    );
  }

  if (!collection) {
    return (
      <div className="pt-32 text-center">
        <Library className="w-12 h-12 mx-auto mb-4 text-white/10" />
        <p className="text-white/40">Collection not found</p>
      </div>
    );
  }

  return (
    <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1440px] mx-auto">
      <Link
        href="/collections"
        className="inline-flex items-center gap-2 text-sm text-white/30 hover:text-white/60 transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Collections
      </Link>

      {/* Hero */}
      <div className="relative rounded-2xl overflow-hidden mb-10">
        <div className="h-48 md:h-56 bg-gradient-to-br from-surface-2 to-surface-1 relative">
          {collection.cover_url && (
            <img
              src={collection.cover_url}
              alt=""
              className="absolute inset-0 w-full h-full object-cover opacity-30"
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-surface-0 via-surface-0/80 to-transparent" />
        </div>
        <div className="absolute bottom-0 left-0 right-0 p-6 md:p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                {collection.is_public ? (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 text-[10px] font-semibold">
                    <Globe className="w-3 h-3" /> Public
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 text-white/30 text-[10px] font-semibold">
                    <Lock className="w-3 h-3" /> Private
                  </span>
                )}
                <span className="text-xs text-white/20">by {collection.owner}</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold font-display mb-1">
                {collection.name}
              </h1>
              {collection.description && (
                <p className="text-sm text-white/40 max-w-xl">{collection.description}</p>
              )}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {collection.is_public && (
                <button
                  onClick={handleShare}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl glass-card text-sm font-medium hover:bg-white/[0.06] transition-colors"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Share2 className="w-4 h-4 text-white/50" />
                  )}
                  {copied ? "Copied!" : "Share"}
                </button>
              )}
              {isOwner && (
                <>
                  <Link
                    href={`/collections/${id}/edit`}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl glass-card text-sm font-medium hover:bg-gold/5 text-gold transition-colors"
                  >
                    <Pencil className="w-3.5 h-3.5" /> Edit
                  </Link>
                  <button
                    onClick={handleDelete}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl glass-card text-sm font-medium hover:bg-red-500/5 text-red-400/70 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Rules pills */}
      {collection.rules && collection.rules.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-8">
          <Filter className="w-4 h-4 text-white/20 mr-1" />
          {collection.rules.map((rule, i) => (
            <span
              key={i}
              className="px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-xs text-white/50"
            >
              <span className="text-gold/70 font-medium">
                {FIELD_LABELS[rule.field] || rule.field}:
              </span>{" "}
              {rule.value}
            </span>
          ))}
          <span className="text-xs text-white/20 ml-2">
            {totalResults.toLocaleString()} movies
          </span>
        </div>
      )}

      {/* Movies grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-5">
          {Array.from({ length: 18 }).map((_, i) => (
            <MovieCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-5">
            {movies.map((movie, i) => (
              <MovieCard
                key={movie.id || movie.tmdb_id}
                movie={movie}
                showOverview
                index={i}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-12">
              <button
                onClick={() => fetchCollection(page - 1)}
                disabled={page <= 1}
                className="px-5 py-2.5 rounded-xl glass-card text-sm font-medium disabled:opacity-20"
              >
                Previous
              </button>
              <span className="text-sm text-white/30 font-mono px-4">
                {page} / {Math.min(totalPages, 500)}
              </span>
              <button
                onClick={() => fetchCollection(page + 1)}
                disabled={page >= totalPages}
                className="px-5 py-2.5 rounded-xl glass-card text-sm font-medium disabled:opacity-20"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}


