import {
  formatRuntime,
  formatCurrency,
  formatDate,
  ratingColor,
  posterUrl,
  backdropUrl,
} from "@/lib/utils";

describe("formatRuntime", () => {
  it("returns hours and minutes for values >= 60", () => {
    expect(formatRuntime(148)).toBe("2h 28m");
  });

  it("returns minutes only for values < 60", () => {
    expect(formatRuntime(45)).toBe("45m");
  });

  it("handles exact hour boundary", () => {
    expect(formatRuntime(120)).toBe("2h 0m");
  });

  it("returns empty string for null", () => {
    expect(formatRuntime(null)).toBe("");
  });

  it("returns empty string for zero", () => {
    expect(formatRuntime(0)).toBe("");
  });
});

describe("posterUrl", () => {
  it("returns placeholder when path is null", () => {
    expect(posterUrl(null)).toBe("/placeholder-poster.svg");
  });

  it("builds TMDB URL with default w500 size", () => {
    expect(posterUrl("/abc.jpg")).toBe(
      "https://image.tmdb.org/t/p/w500/abc.jpg"
    );
  });

  it("builds TMDB URL with w185 size", () => {
    expect(posterUrl("/abc.jpg", "w185")).toBe(
      "https://image.tmdb.org/t/p/w185/abc.jpg"
    );
  });

  it("passes through full http URLs unchanged", () => {
    const url = "https://example.com/poster.jpg";
    expect(posterUrl(url)).toBe(url);
  });
});

describe("backdropUrl", () => {
  it("returns empty string when path is null", () => {
    expect(backdropUrl(null)).toBe("");
  });

  it("builds w1280 TMDB URL", () => {
    expect(backdropUrl("/back.jpg")).toBe(
      "https://image.tmdb.org/t/p/w1280/back.jpg"
    );
  });

  it("passes through full http URLs unchanged", () => {
    const url = "https://example.com/backdrop.jpg";
    expect(backdropUrl(url)).toBe(url);
  });
});

describe("ratingColor", () => {
  it("returns emerald for ratings >= 8", () => {
    expect(ratingColor(8.5)).toBe("text-emerald-400");
    expect(ratingColor(8.0)).toBe("text-emerald-400");
  });

  it("returns amber for ratings >= 6 and < 8", () => {
    expect(ratingColor(7.9)).toBe("text-amber-300");
    expect(ratingColor(6.0)).toBe("text-amber-300");
  });

  it("returns orange for ratings >= 4 and < 6", () => {
    expect(ratingColor(5.5)).toBe("text-orange-400");
    expect(ratingColor(4.0)).toBe("text-orange-400");
  });

  it("returns red for ratings < 4", () => {
    expect(ratingColor(3.9)).toBe("text-red-400");
    expect(ratingColor(0)).toBe("text-red-400");
  });
});

describe("formatCurrency", () => {
  it("returns em dash for zero", () => {
    expect(formatCurrency(0)).toBe("—");
  });

  it("formats large numbers as USD", () => {
    const result = formatCurrency(63_000_000);
    expect(result).toContain("$");
    expect(result).toContain("63,000,000");
  });
});

describe("formatDate", () => {
  it("returns empty string for empty input", () => {
    expect(formatDate("")).toBe("");
  });

  it("formats ISO date to readable US format", () => {
    const result = formatDate("1999-10-15");
    expect(result).toContain("1999");
    expect(result).toContain("October");
    expect(result).toContain("15");
  });
});
