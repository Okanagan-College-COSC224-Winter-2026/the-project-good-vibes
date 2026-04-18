import { useMemo } from "react";
import { Outlet, useParams } from "react-router-dom";
import TabNavigation from "../ui/TabNavigation";
import Button from "../ui/Button";
import { useClasses } from "../features/classes/useClasses";
import { importCSV } from "../util/csv";
import { isTeacher } from "../util/login";

export default function ClassLayout() {
  const { id } = useParams();
  const { data: classes = [] } = useClasses();

  const className = useMemo(() => {
    return classes.find((c: { id: number }) => c.id === Number(id))?.name || null;
  }, [classes, id]);

  return (
    <>
      <div className="flex flex-row justify-between items-center px-5 md:px-8 py-4 border-b border-border gap-4 bg-white">
        <h2 className="text-xl font-semibold text-text-primary min-w-0 truncate m-0">{className}</h2>
        <div className="flex-shrink-0">
          {isTeacher() ? (
            <Button onClick={() => importCSV(id as string)}>
              <span className="hidden sm:inline">Add Students via CSV</span>
              <span className="sm:hidden">+ CSV</span>
            </Button>
          ) : null}
        </div>
      </div>

      <TabNavigation
        tabs={[
          { label: "Assignments", path: `/classes/${id}/home` },
          { label: "Members", path: `/classes/${id}/members` },
          { label: "Groups", path: `/classes/${id}/groups` },
          ...(isTeacher() ? [
            { label: "Gradebook", path: `/classes/${id}/gradebook` },
          ] : [
            { label: "My Evaluations", path: `/classes/${id}/evaluations` },
          ]),
          ...(isTeacher() ? [{ label: "Settings", path: `/classes/${id}/settings` }] : []),
        ]}
      />

      <Outlet />
    </>
  );
}
