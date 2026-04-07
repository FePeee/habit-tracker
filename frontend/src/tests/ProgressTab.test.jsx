import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, cleanup } from "@testing-library/react";
import ProgressTab from "../pages/ProgressTab";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    getAIInsights: vi.fn(),
    deleteAIInsight: vi.fn(),
  },
}));

afterEach(() => cleanup());

describe("ProgressTab", () => {
  const mockInsights = [
    {
      id: 1,
      insight_type: "habit_advice",
      content: "💡 Try reading 10 minutes before bed. It's a small habit that compounds over time.",
      habit_id: 1,
      habit_name: "Reading",
      context: "Habit: Reading, Issue: not enough time",
      created_at: "2024-01-15T10:00:00",
    },
    {
      id: 2,
      insight_type: "role_model",
      content: "🎭 Software engineers should code daily, read technical docs, and build side projects to stay sharp.",
      habit_id: null,
      habit_name: null,
      context: "Role: Software Engineer",
      created_at: "2024-01-16T14:30:00",
    },
    {
      id: 3,
      insight_type: "suggest_habits",
      content: "✨ Morning routine: 1) Meditate 5 min, 2) Write 3 gratitudes, 3) Plan top 3 tasks for the day.",
      habit_id: null,
      habit_name: null,
      context: "Morning productivity",
      created_at: "2024-01-17T08:00:00",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    api.getAIInsights.mockReturnValue(new Promise(() => {})); // Never resolves
    render(<ProgressTab />);
    expect(screen.getByText(/loading insights/i)).toBeTruthy();
  });

  it("displays insights when loaded", async () => {
    api.getAIInsights.mockResolvedValue(mockInsights);
    render(<ProgressTab />);

    await waitFor(() => {
      expect(screen.getByText("💡 Habit Advice")).toBeTruthy();
      expect(screen.getByText("🎭 Role Model")).toBeTruthy();
      expect(screen.getByText("✨ Suggestions")).toBeTruthy();
    });

    expect(screen.getByText(/Try reading 10 minutes before bed/i)).toBeTruthy();
  });

  it("shows empty state when no insights", async () => {
    api.getAIInsights.mockResolvedValue([]);
    render(<ProgressTab />);

    await waitFor(() => {
      expect(screen.getByText(/no insights yet/i)).toBeTruthy();
    });

    expect(screen.getByText(/\/advise/i)).toBeTruthy();
    expect(screen.getByText(/\/rolemodel/i)).toBeTruthy();
  });

  it("filters insights by type when filter button clicked", async () => {
    api.getAIInsights.mockResolvedValue(mockInsights);
    render(<ProgressTab />);

    await waitFor(() => {
      expect(screen.getByText("💡 Habit Advice (1)")).toBeTruthy();
    });

    // Click filter button for habit_advice
    const filterButton = screen.getByText("💡 Habit Advice (1)");
    fireEvent.click(filterButton);

    // Should only show habit_advice insight
    await waitFor(() => {
      expect(screen.queryByText("🎭 Role Model")).toBeFalsy();
      expect(screen.queryByText("✨ Suggestions")).toBeFalsy();
    });
  });

  it("deletes insight when delete button clicked", async () => {
    api.getAIInsights.mockResolvedValue(mockInsights);
    api.deleteAIInsight.mockResolvedValue({ message: "Deleted" });

    // Mock window.confirm
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<ProgressTab />);

    await waitFor(() => {
      expect(screen.getByText("💡 Habit Advice")).toBeTruthy();
    });

    // Click delete button (×)
    const deleteButtons = screen.getAllByText("×");
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(api.deleteAIInsight).toHaveBeenCalledWith(1);
    });
  });

  it("shows summary statistics", async () => {
    api.getAIInsights.mockResolvedValue(mockInsights);
    render(<ProgressTab />);

    await waitFor(() => {
      expect(screen.getByText("3")).toBeTruthy(); // Total insights
    });

    // Check type counts
    expect(screen.getByText("1")).toBeTruthy(); // habit_advice count
  });
});
