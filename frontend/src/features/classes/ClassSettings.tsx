import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import Modal from "../../ui/Modal";
import { useClasses, useUpdateCourse, useUploadCourseImage, useDeleteCourse } from "./useClasses";
import { getCourseImageUrl } from "../../services/classApi";

interface SettingsFormData {
  name: string;
}

export default function ClassSettings() {
  const { id } = useParams();
  const courseId = Number(id);

  const { data: classes = [] } = useClasses();
  const course = classes.find((c: { id: number }) => c.id === courseId);

  const { register, handleSubmit, reset } = useForm<SettingsFormData>();
  const { mutate: updateCourse, isPending: isSaving } = useUpdateCourse(courseId);
  const { mutate: uploadImage, isPending: isUploading } = useUploadCourseImage(courseId);

  const { mutate: deleteCourse, isPending: isDeleting } = useDeleteCourse();
  const navigate = useNavigate();

  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (course) {
      reset({ name: course.name || "" });
    }
  }, [course, reset]);

  const currentImageSrc =
    imagePreview ?? (course?.image_path ? getCourseImageUrl(courseId) : null);

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  }

  function onSubmit(data: SettingsFormData) {
    // Upload image first if selected, then update name
    if (imageFile) {
      uploadImage(imageFile, {
        onSuccess: () => {
          setImageFile(null);
          // Now update name
          updateCourse(
            { name: data.name },
            {
              onSuccess: () => toast.success("Course updated successfully."),
              onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to update course."),
            }
          );
        },
        onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to upload image."),
      });
    } else {
      updateCourse(
        { name: data.name },
        {
          onSuccess: () => toast.success("Course updated successfully."),
          onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to update course."),
        }
      );
    }
  }

  function handleCancel() {
    reset({ name: course?.name || "" });
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  const isPending = isSaving || isUploading;

  return (
    <div className="p-4 md:p-8 w-full max-w-260 mx-auto flex flex-col gap-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-text-primary m-0">Course Settings</h2>
      </div>

      {/* Settings card */}
      <div className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
        <div className="px-5 md:px-8 py-4 border-b border-border">
          <h3 className="text-base font-semibold text-text-primary m-0">Course Details</h3>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="px-5 md:px-8 py-6 flex flex-col gap-6">
          {/* Cover image */}
          <div className="flex flex-col gap-3">
            <span className="text-sm font-medium text-text-primary">Cover image</span>
            <div className="flex flex-col sm:flex-row items-start gap-4">
              <div className="w-full sm:w-48 h-32 rounded-xl bg-bg-secondary border border-border overflow-hidden flex-shrink-0">
                {currentImageSrc ? (
                  <img
                    src={currentImageSrc}
                    alt="Course cover"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-text-secondary text-sm">
                    No image
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <label className="cursor-pointer">
                  <span className="inline-flex items-center px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors">
                    {imageFile ? imageFile.name : "Choose image"}
                  </span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/gif,image/webp"
                    className="hidden"
                    onChange={handleImageSelect}
                  />
                </label>
                <p className="text-xs text-text-secondary m-0">PNG, JPG, GIF or WebP. Displayed on the dashboard card.</p>
                {imageFile && (
                  <button
                    type="button"
                    className="self-start text-xs text-text-secondary hover:text-red-600 bg-transparent border-none cursor-pointer"
                    onClick={() => {
                      setImageFile(null);
                      setImagePreview(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                  >
                    Remove selection
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Course name */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary">Course name</label>
            <input
              type="text"
              disabled={isPending}
              className="px-3.5 py-2.5 border border-border rounded-lg bg-bg-secondary text-text-primary text-sm font-[inherit] w-full focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all disabled:opacity-60"
              {...register("name", { required: true })}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-4 border-t border-border">
            <button
              type="button"
              onClick={handleCancel}
              disabled={isPending}
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="px-5 py-2 rounded-lg bg-btn-primary text-white text-sm font-semibold hover:brightness-110 active:scale-[0.98] transition-all cursor-pointer border-none disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isPending ? "Saving..." : "Update course"}
            </button>
          </div>
        </form>
      </div>
      {/* Danger Zone */}
      <div className="bg-white rounded-2xl border border-red-200 shadow-sm overflow-hidden">
        <div className="px-5 md:px-8 py-4 border-b border-red-200 bg-red-50/50">
          <h3 className="text-base font-semibold text-red-700 m-0">Danger Zone</h3>
        </div>
        <div className="px-5 md:px-8 py-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-text-primary m-0 mb-0.5">Delete this course</p>
              <p className="text-xs text-text-secondary m-0">Permanently remove this course and all its assignments, groups, rubrics, and student enrollments.</p>
            </div>
            <button
              onClick={() => setIsDeleteModalOpen(true)}
              className="flex-shrink-0 px-4 py-2 rounded-lg border border-red-300 text-sm font-medium text-red-600 hover:bg-red-600 hover:text-white transition-colors cursor-pointer bg-transparent"
            >
              Delete course
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Delete Course">
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">
            Are you sure you want to delete <strong className="text-text-primary">{course?.name}</strong>? All assignments, groups, rubrics, reviews, and student enrollments will be permanently removed. This action cannot be undone.
          </p>
          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={() => setIsDeleteModalOpen(false)}
              className="inline-flex items-center px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent"
            >
              Cancel
            </button>
            <button
              disabled={isDeleting}
              onClick={() => {
                deleteCourse(courseId, {
                  onSuccess: () => {
                    toast.success("Course deleted.");
                    navigate("/home");
                  },
                  onError: (error) => {
                    toast.error(error instanceof Error ? error.message : "Failed to delete course.");
                    setIsDeleteModalOpen(false);
                  },
                });
              }}
              className="inline-flex items-center px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold border-none cursor-pointer transition-all duration-150 hover:bg-red-700 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
