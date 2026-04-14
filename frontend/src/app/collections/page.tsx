"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Library, Plus, Globe, Lock, Trash2, Pencil, Loader2, Layers,
} from "lucide-react";
import { collectionsAPI } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import type { CollectionCompact } from "@/types/movie";

export default function CollectionsPage() {
  const { isAuthenticated } = useAuth();
  const [collections, setCollections] = useState<CollectionCompact[]>([]);
  const [publicCollections, setPublicCollections] = useState<CollectionCompact[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"mine" | "public">("mine");

  useEffect(() => {
    fetchCollections();
  }, [isAuthenticated]);

  async function fetchCollections() {
    setLoading(true);
    try {
      const [mine, pub] = await Promise.allSettled([
        isAuthenticated ? collectionsAPI.list() : Promise.resolve([]),
        collectionsAPI.getPublicList(),
      ]);
      if (mine.status === "fulfilled") setCollections(mine.value);
      if (pub.status === "fulfilled") setPublicCollections(pub.value);
    } catch (err) {
      console.error("Failed to load collections", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this collection?")) return;
    try {
      await collectionsAPI.delete(id);
      setCollections((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error("Failed to delete", err);
    }
  }

  const activeList = tab === "mine" ? collections : publicCollections;

  return (
    <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold/10 border border-gold/15 mb-4">
            <Library className="w-3.5 h-3.5 text-gold" />
            <span className="text-[11px] font-semibold uppercase tracking-widest text-gold">
              Smart Collections
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold font-display mb-2">
            Your <span className="text-gold italic">Collections</span>
          </h1>
          <p className="text-white/35 max-w-lg">
            Create dynamic movie lists powered by genre, era, rating, and runtime filters.
            Collections update automatically as new movies match your rules.
          </p>
        </div>
        {isAuthenticated && (
          <Link
            href="/collections/new"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold to-gold-dim text-surface-0 text-sm font-semibold hover:shadow-lg hover:shadow-gold/15 transition-all shrink-0"
          >
            <Plus className="w-4 h-4" />
            New Collection
          </Link>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-8 p-1 rounded-xl bg-white/[0.03] border border-white/[0.06] w-fit">
        <button
          onClick={() => setTab("mine")}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
            tab === "mine"
              ? "bg-gold/15 text-gold border border-gold/20"
              : "text-white/40 hover:text-white/60"
          }`}
        >
          My Collections
        </button>
        <button
          onClick={() => setTab("public")}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
            tab === "public"
              ? "bg-gold/15 text-gold border border-gold/20"
              : "text-white/40 hover:text-white/60"
          }`}
        >
          <Globe className="w-3.5 h-3.5 inline mr-1.5" />
          Public
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-gold/40" />
        </div>
      ) : activeList.length === 0 ? (
        <div className="text-center py-20">
          <Layers className="w-12 h-12 mx-auto mb-4 text-white/10" />
          <p className="text-white/30 mb-4">
            {tab === "mine"
              ? "You haven't created any collections yet."
              : "No public collections available."}
          </p>
          {tab === "mine" && isAuthenticated && (
            <Link
              href="/collections/new"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl glass-card text-sm font-medium text-gold hover:bg-gold/5 transition-all"
            >
              <Plus className="w-4 h-4" />
              Create your first collection
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {activeList.map((col) => (
            <Link
              key={col.id}
              href={`/collections/${col.id}`}
              className="glass-card group relative overflow-hidden rounded-2xl transition-all duration-300 hover:ring-1 hover:ring-gold/20"
            >
              {/* Cover */}
              <div className="h-36 bg-gradient-to-br from-surface-2 to-surface-1 relative overflow-hidden">
                {col.cover_url && (
                  <img
                    src={col.cover_url}
                    alt=""
                    className="absolute inset-0 w-full h-full object-cover opacity-40 group-hover:opacity-60 transition-opacity"
                  />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-surface-0 via-surface-0/60 to-transparent" />
                <div className="absolute top-3 right-3 flex gap-1.5">
                  {col.is_public ? (
                    <span className="px-2 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 text-[10px] font-semibold flex items-center gap-1">
                      <Globe className="w-3 h-3" /> Public
                    </span>
                  ) : (
                    <span className="px-2 py-1 rounded-lg bg-white/5 text-white/30 text-[10px] font-semibold flex items-center gap-1">
                      <Lock className="w-3 h-3" /> Private
                    </span>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="p-5 pt-3">
                <h3 className="text-lg font-bold font-display mb-1 group-hover:text-gold transition-colors">
                  {col.name}
                </h3>
                {col.description && (
                  <p className="text-sm text-white/30 line-clamp-2 mb-3">{col.description}</p>
                )}
                <div className="flex items-center justify-between text-xs text-white/20">
                  <span>{col.rule_count} rule{col.rule_count !== 1 ? "s" : ""}</span>
                  <span>by {col.owner}</span>
                </div>
              </div>

              {/* Actions (only for own collections) */}
              {tab === "mine" && (
                <div className="absolute top-3 left-3 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Link
                    href={`/collections/${col.id}/edit`}
                    onClick={(e) => e.stopPropagation()}
                    className="w-8 h-8 rounded-lg bg-white/10 backdrop-blur flex items-center justify-center hover:bg-gold/20 transition-colors"
                  >
                    <Pencil className="w-3.5 h-3.5 text-white/70" />
                  </Link>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleDelete(col.id);
                    }}
                    className="w-8 h-8 rounded-lg bg-white/10 backdrop-blur flex items-center justify-center hover:bg-red-500/20 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-white/70" />
                  </button>
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
