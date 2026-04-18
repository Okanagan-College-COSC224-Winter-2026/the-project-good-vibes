import { describe, expect, it, vi } from "vitest";
import { formatDueDate, getAssignmentStatus } from "./assignmentDates";

describe("assignmentDates", () => {
  describe("formatDueDate", () => {
    it("returns fallback when due date is missing", () => {
      expect(formatDueDate()).toBe("No due date");
    });

    it("returns invalid marker for malformed due date", () => {
      expect(formatDueDate("not-a-date")).toBe("Invalid due date");
    });

    it("formats valid due dates", () => {
      expect(formatDueDate("2026-01-01T00:00:00.000Z")).toBeTruthy();
    });
  });

  describe("getAssignmentStatus", () => {
    it("returns no due date when missing", () => {
      expect(getAssignmentStatus()).toBe("No due date");
    });

    it("returns no due date for invalid dates", () => {
      expect(getAssignmentStatus("invalid-date")).toBe("No due date");
    });

    it("returns overdue for past dates", () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date("2026-01-02T00:00:00.000Z"));

      expect(getAssignmentStatus("2026-01-01T00:00:00.000Z")).toBe("Overdue");

      vi.useRealTimers();
    });

    it("returns upcoming for future dates", () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date("2026-01-01T00:00:00.000Z"));

      expect(getAssignmentStatus("2026-01-02T00:00:00.000Z")).toBe("Upcoming");

      vi.useRealTimers();
    });
  });
});
