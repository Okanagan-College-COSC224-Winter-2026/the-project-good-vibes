import { useState, useRef, useEffect } from "react";

interface GradeCellProps {
  effectiveGrade: number | null;
  effectiveMax: number | null;
  isOverridden: boolean;
  onSetOverride: (score: number) => void;
  onClearOverride: () => void;
  onClickDetails: () => void;
}

export default function GradeCell({
  effectiveGrade,
  effectiveMax,
  isOverridden,
  onSetOverride,
  onClearOverride,
  onClickDetails,
}: GradeCellProps) {
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const startEdit = () => {
    const pct =
      effectiveMax && effectiveMax > 0 && effectiveGrade !== null
        ? ((effectiveGrade / effectiveMax) * 100).toFixed(0)
        : "";
    setEditValue(pct);
    setEditing(true);
  };

  const commitEdit = () => {
    setEditing(false);
    const trimmed = editValue.trim();
    if (trimmed === "") {
      if (isOverridden) onClearOverride();
      return;
    }
    const pct = parseFloat(trimmed);
    if (!isNaN(pct) && pct >= 0 && pct <= 100) {
      // Skip save if the percentage didn't actually change
      const currentPct =
        effectiveMax && effectiveMax > 0 && effectiveGrade !== null
          ? Math.round((effectiveGrade / effectiveMax) * 100)
          : null;
      if (Math.round(pct) === currentPct) return;

      const raw = effectiveMax && effectiveMax > 0 ? (pct / 100) * effectiveMax : pct;
      onSetOverride(raw);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") commitEdit();
    if (e.key === "Escape") setEditing(false);
  };

  if (effectiveGrade === null && !editing) {
    return (
      <td className="px-4 py-3 text-center">
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={startEdit}
            className="bg-transparent border-none cursor-pointer text-text-secondary text-xs px-2 py-1 rounded-lg transition-colors hover:bg-bg-secondary"
            title="Click to set override"
          >
            --
          </button>
          <button
            onClick={onClickDetails}
            className="bg-transparent border-none cursor-pointer text-text-secondary hover:text-btn-primary transition-colors p-1 rounded-lg hover:bg-bg-secondary"
            title="View reviews"
          >
            <EyeIcon />
          </button>
        </div>
      </td>
    );
  }

  const percentage =
    effectiveMax && effectiveMax > 0 && effectiveGrade !== null
      ? ((effectiveGrade / effectiveMax) * 100).toFixed(0)
      : null;

  return (
    <td className="px-4 py-3">
      <div className="flex items-center justify-center gap-2">
        {editing ? (
          <input
            ref={inputRef}
            type="number"
            step="any"
            min="0"
            max="100"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={commitEdit}
            onKeyDown={handleKeyDown}
            className="w-16 text-center text-sm font-semibold border border-border rounded-lg px-2 py-1 bg-white text-text-primary outline-none focus:border-btn-primary"
          />
        ) : (
          <button
            onClick={startEdit}
            className={`bg-transparent border-none cursor-pointer text-sm font-semibold px-2 py-1 rounded-lg transition-colors hover:bg-bg-secondary ${
              isOverridden ? "text-amber-600" : "text-text-primary"
            }`}
            title={isOverridden ? "Teacher override (click to edit)" : "Peer review average (click to override)"}
          >
            {percentage !== null ? `${percentage}%` : effectiveGrade}
          </button>
        )}
        {isOverridden && !editing ? (
          <button
            onClick={onClearOverride}
            className="bg-transparent border-none cursor-pointer text-amber-600 hover:text-red-500 transition-colors p-1 rounded-lg hover:bg-bg-secondary"
            title="Revert to peer review grade"
          >
            <UndoIcon />
          </button>
        ) : (
          <button
            onClick={onClickDetails}
            className="bg-transparent border-none cursor-pointer text-text-secondary hover:text-btn-primary transition-colors p-1 rounded-lg hover:bg-bg-secondary"
            title="View reviews"
          >
            <EyeIcon />
          </button>
        )}
      </div>
    </td>
  );
}

function UndoIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="1 4 1 10 7 10" />
      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}
