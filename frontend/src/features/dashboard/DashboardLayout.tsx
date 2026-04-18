import { useState, useMemo, useEffect } from "react";
import ClassCard from "../classes/ClassCard";
import { useClassesWithAssignments } from "../classes/useClasses";
import { useDebounce } from "../../hooks/useDebounce";
import { isTeacher, isAdmin } from "../../util/login";
import { getCourseImageUrl } from "../../services/classApi";
import { getCourseGradeSummary } from "../../services/reviewApi";

export default function DashboardLayout() {
  const {
    data: courses = [],
    isLoading
  } = useClassesWithAssignments();

  const [grades, setGrades] = useState<Record<number, string>>({});

  useEffect(() => {
    courses.forEach(async (course: CourseWithAssignments) => {
      try {
        const data = await getCourseGradeSummary(course.id);
        const pcts = (data.assignments ?? [])
          .map((a: { individualAverage: number | null; individualMax: number | null; groupAverage: number | null; groupMax: number | null }) => {
            const typePcts: number[] = [];
            if (a.individualAverage != null && a.individualMax && a.individualMax > 0) { typePcts.push(a.individualAverage / a.individualMax); }
            if (a.groupAverage != null && a.groupMax && a.groupMax > 0) { typePcts.push(a.groupAverage / a.groupMax); }
            return typePcts.length > 0 ? typePcts.reduce((s, p) => s + p, 0) / typePcts.length : null;
          })
          .filter((p: number | null): p is number => p !== null);
        const pct = pcts.length > 0 ? Math.round(pcts.reduce((s: number, p: number) => s + p, 0) / pcts.length * 100) : null;
        setGrades(prev => ({
          ...prev,
          [course.id]: pct !== null ? `Grade: ${pct}%` : `Grade: N/A`
        }));
      } catch {
        // no grade available yet
      }
    });
  }, [courses]);
  

  const [searchQuery, setSearchQuery] = useState("");
  const debouncedQuery = useDebounce(searchQuery, 300);

  const filteredCourses = useMemo(() => {
    const q = debouncedQuery.trim().toLowerCase();
    if (!q) return courses;
    return courses.filter((course: CourseWithAssignments) =>
      course.name.toLowerCase().includes(q)
    );
  }, [courses, debouncedQuery]);

  if (isLoading) {
    return (
      <div className="p-6 md:p-8 w-full">
        <h1 className="text-2xl font-bold text-text-primary border-b border-border pb-3 mb-6">Peer Review Dashboard</h1>
        <p className="text-text-secondary">Loading courses...</p>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 w-full max-w-[85vw] sm:max-w-260 mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4 mb-6">
        <h1 className="text-2xl font-bold text-text-primary m-0">Peer Review Dashboard</h1>

        {/* Search bar */}
        <div className="relative w-full sm:w-80">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            className="w-full px-4 py-2.5 rounded-lg bg-white text-sm text-text-primary placeholder:text-text-secondary border border-border shadow-sm focus:outline-none focus:border-btn-primary focus:shadow-md transition-all duration-200"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary bg-transparent border-none cursor-pointer text-xs transition-colors"
            >
              &#10005;
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 items-stretch">
        {filteredCourses.map((course: CourseWithAssignments) => (
          <ClassCard
            key={course.id}
            image={course.image_path ? getCourseImageUrl(course.id) : "https://crc.losrios.edu//shared/img/social-1200-630/programs/general-science-social.jpg"}
            name={course.name}
            subtitle={`${course.assignmentCount || 0} assignments`}
            href={`/classes/${course.id}/home`}
            grade={!isTeacher() ? grades[course.id] : undefined}
          />
        ))}

        {isTeacher() && !debouncedQuery && (
          <div
            className="size-full min-h-[13rem] flex flex-col items-center justify-center gap-2 bg-bg-secondary text-text-secondary rounded-xl border-2 border-dashed border-bg-tertiary transition-all duration-150 hover:border-btn-primary hover:text-btn-primary hover:bg-emerald-50 cursor-pointer"
            onClick={() => window.location.href = '/classes/create'}
          >
            <span className="text-2xl font-light">+</span>
            <span className="text-sm font-medium">Create Class</span>
          </div>
        )}

        {isAdmin() && !debouncedQuery && (
          <div
            className="size-full min-h-[13rem] flex flex-col items-center justify-center gap-2 bg-bg-secondary text-text-secondary rounded-xl border-2 border-dashed border-bg-tertiary transition-all duration-150 hover:border-btn-secondary hover:text-btn-secondary hover:bg-slate-200 cursor-pointer"
            onClick={() => window.location.href = '/admin/create-teacher'}
          >
            <span className="text-2xl font-light">+</span>
            <span className="text-sm font-medium">Create Teacher</span>
          </div>
        )}
      </div>

      {debouncedQuery && filteredCourses.length === 0 && (
        <p className="text-text-secondary text-sm mt-6 text-center">No courses matching "{debouncedQuery}"</p>
      )}
    </div>
  );
}
