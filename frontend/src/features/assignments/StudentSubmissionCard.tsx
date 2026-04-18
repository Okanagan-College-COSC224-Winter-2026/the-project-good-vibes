import { useState } from "react";
import toast from "react-hot-toast";
import { useUploadSubmission, useDeleteSubmission } from "../reviews/useSubmission";
import { cardClass, btnSecondary, btnOutline } from "./assignmentStyles";

interface Props {
  assignmentId: number;
  mySubmission: { download_url: string; filename: string } | null;
}

export default function StudentSubmissionCard({ assignmentId, mySubmission }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const { mutate: uploadSubmission, isPending: isUploading } = useUploadSubmission(assignmentId);
  const { mutate: deleteSubmission } = useDeleteSubmission(assignmentId);

  return (
    <div className={cardClass}>
      <div className="px-5 md:px-8 py-4 border-b border-border">
        <h3 className="text-base font-semibold text-text-primary m-0">Submit Your Assignment</h3>
      </div>

      <div className="px-5 md:px-8 py-5 flex flex-col gap-5">
        <div>
          <h4 className="text-sm font-semibold text-text-primary m-0 mb-3">My Attachment</h4>
          {mySubmission ? (
            <div className="flex items-center gap-3 mb-3">
              <a href={mySubmission.download_url} target="_blank" rel="noreferrer" className="text-btn-primary text-sm hover:underline">
                {mySubmission.filename}
              </a>
              <button
                className={btnOutline}
                onClick={() => {
                  deleteSubmission(undefined, {
                    onSuccess: () => {
                      setSelectedFile(null);
                      toast.success("Attachment removed.");
                    },
                    onError: (error) => toast.error(error instanceof Error ? error.message : "Failed to remove attachment."),
                  });
                }}
              >
                Remove
              </button>
            </div>
          ) : (
            <p className="text-text-secondary text-sm m-0 mb-3">No attachment uploaded yet.</p>
          )}

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 pt-3">
            <label className="flex-1 cursor-pointer">
              <div className="flex items-center justify-center px-4 py-3 rounded-lg border-2 border-dashed border-border hover:border-btn-primary/40 hover:bg-btn-primary/5 transition-all">
                <span className="text-sm text-text-secondary">
                  {selectedFile ? selectedFile.name : "Choose a file..."}
                </span>
              </div>
              <input
                type="file"
                className="hidden"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
            </label>
            <button
              className={btnSecondary}
              disabled={isUploading || !selectedFile}
              onClick={() => {
                if (!selectedFile) {
                  toast.error("Please choose a file first.");
                  return;
                }
                uploadSubmission(selectedFile, {
                  onSuccess: () => {
                    setSelectedFile(null);
                    toast.success(mySubmission ? "Attachment updated." : "Attachment uploaded.");
                  },
                  onError: (error) => toast.error(error instanceof Error ? error.message : "Failed to upload attachment."),
                });
              }}
            >
              {isUploading ? "Submitting..." : "Submit!"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
