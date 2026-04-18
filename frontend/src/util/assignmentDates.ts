export type AssignmentStatus = "No due date" | "Upcoming" | "Overdue" | "Submitted";
export type TeacherAssignmentStatus = "No due date" | "Open" | "Closed";

// Backend returns naive UTC datetimes (no Z suffix).
// Append Z so JavaScript parses them as UTC, not local time.
function ensureUTC(dateStr: string): string {
  return dateStr.endsWith("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
}

export function formatDueDate(dueDate?: string): string {
  if (!dueDate) {
    return "No due date";
  }

  const parsed = new Date(ensureUTC(dueDate));
  if (Number.isNaN(parsed.getTime())) {
    return "Invalid due date";
  }

  return parsed.toLocaleDateString();
}

export function getAssignmentStatus(dueDate?: string, hasSubmitted?: boolean): AssignmentStatus {
  if (hasSubmitted) {
    return "Submitted";
  }

  if (!dueDate) {
    return "No due date";
  }

  const parsed = new Date(ensureUTC(dueDate));
  if (Number.isNaN(parsed.getTime())) {
    return "No due date";
  }

  return parsed.getTime() < Date.now() ? "Overdue" : "Upcoming";
}

export function getTeacherAssignmentStatus(dueDate?: string): TeacherAssignmentStatus {
  if (!dueDate) {
    return "No due date";
  }

  const parsed = new Date(ensureUTC(dueDate));
  if (Number.isNaN(parsed.getTime())) {
    return "No due date";
  }

  return parsed.getTime() < Date.now() ? "Closed" : "Open";
}