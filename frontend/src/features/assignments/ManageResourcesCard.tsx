import { useState } from "react";
import toast from "react-hot-toast";
import { useUploadAssignmentResource, useDeleteAssignmentResource } from "./useAssignments";
import { cardClass, btnSecondary } from "./assignmentStyles";
import type { AssignmentResourceItem } from "./useAssignmentDetail";

interface Props {
  assignmentId: number;
  resources: AssignmentResourceItem[];
}

export default function ManageResourcesCard({ assignmentId, resources }: Props) {
  const [resourceUpload, setResourceUpload] = useState<File | null>(null);

  const { mutate: uploadResource, isPending: isUploading } = useUploadAssignmentResource(assignmentId);
  const { mutate: deleteResource } = useDeleteAssignmentResource(assignmentId);

  return (
    <div className={cardClass}>
      <div className="px-5 md:px-8 py-4 border-b border-border">
        <h3 className="text-base font-semibold text-text-primary m-0">Supporting Documents</h3>
      </div>

      <div className="px-5 md:px-8 py-5 flex flex-col gap-5">
        {resources.length === 0 ? (
          <p className="text-text-secondary text-sm m-0">No documents uploaded yet.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {resources.map((resource) => (
              <div key={resource.id} className="flex items-center justify-between gap-3 px-4 py-3 rounded-lg bg-bg-secondary border border-border">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-btn-primary/10 flex items-center justify-center text-btn-primary text-xs font-bold">
                    {resource.original_name.split('.').pop()?.toUpperCase().slice(0, 3)}
                  </span>
                  <a href={resource.download_url} target="_blank" rel="noreferrer" className="text-text-primary text-sm font-medium hover:text-btn-primary hover:underline truncate transition-colors">
                    {resource.original_name}
                  </a>
                </div>
                <button
                  className="flex-shrink-0 text-xs px-2.5 py-1 rounded-md text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 cursor-pointer transition-colors"
                  onClick={() => {
                    deleteResource(resource.id, {
                      onSuccess: () => toast.success("Document deleted."),
                      onError: (error) => toast.error(error instanceof Error ? error.message : "Failed to delete document."),
                    });
                  }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="pt-4 border-t border-border">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide m-0 mb-3">Upload new document</p>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <label className="flex-1 cursor-pointer">
              <div className="flex items-center justify-center px-4 py-3 rounded-lg border-2 border-dashed border-border hover:border-btn-primary/40 hover:bg-btn-primary/5 transition-all">
                <span className="text-sm text-text-secondary">
                  {resourceUpload ? resourceUpload.name : "Choose a file..."}
                </span>
              </div>
              <input
                type="file"
                className="hidden"
                onChange={(e) => setResourceUpload(e.target.files?.[0] || null)}
              />
            </label>
            <button
              className={btnSecondary}
              disabled={isUploading || !resourceUpload}
              onClick={() => {
                if (!resourceUpload) return;
                uploadResource(resourceUpload, {
                  onSuccess: () => {
                    setResourceUpload(null);
                    toast.success("Document uploaded.");
                  },
                  onError: (error) => toast.error(error instanceof Error ? error.message : "Failed to upload document."),
                });
              }}
            >
              {isUploading ? "Uploading..." : "Upload"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
