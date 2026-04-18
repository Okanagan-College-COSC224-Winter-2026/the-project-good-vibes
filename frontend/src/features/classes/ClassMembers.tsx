import { useParams } from "react-router-dom";
import { useCourseMembers } from "./useClasses";

export default function ClassMembers() {
  const { id } = useParams()
  const { data: members = [], isLoading } = useCourseMembers(id as string);

  return (
    <div className="p-4 md:p-8 w-full max-w-260 mx-auto flex flex-col gap-6">
      <h2 className="text-2xl font-semibold text-text-primary m-0">Members</h2>

      <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
        <div className="px-5 md:px-8 py-4 border-b border-border flex items-center justify-between">
          <h3 className="text-base font-semibold text-text-primary m-0">Enrolled Students</h3>
          <span className="text-xs font-medium text-text-secondary bg-bg-secondary px-2.5 py-1 rounded-full">
            {members.length} member{members.length !== 1 ? "s" : ""}
          </span>
        </div>

        {isLoading ? (
          <div className="px-5 md:px-8 py-8 text-center">
            <p className="text-text-secondary text-sm m-0">Loading members...</p>
          </div>
        ) : members.length === 0 ? (
          <div className="px-5 md:px-8 py-8 flex flex-col items-center gap-2">
            <span className="text-3xl">👥</span>
            <p className="text-text-secondary text-sm m-0">No members enrolled yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {members.map((member: User) => (
              <div
                key={member.id}
                className="px-5 md:px-8 py-3.5 flex items-center gap-3 transition-colors hover:bg-btn-primary/[0.03]"
              >
                <div className="w-9 h-9 rounded-full bg-btn-primary/10 flex items-center justify-center text-sm font-semibold text-btn-primary flex-shrink-0">
                  {member.name.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <span className="text-sm font-medium text-text-primary block truncate">{member.name}</span>
                  {member.email && (
                    <span className="text-xs text-text-secondary block truncate">{member.email}</span>
                  )}
                </div>
                <span className="text-xs text-text-secondary font-mono flex-shrink-0">#{member.id}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
