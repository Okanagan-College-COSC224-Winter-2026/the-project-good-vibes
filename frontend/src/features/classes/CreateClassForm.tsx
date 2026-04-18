import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useCreateClass } from "./useClasses";
import { uploadCourseImage } from "../../services/classApi";

interface CreateFormData {
  name: string;
}

export default function CreateClassForm() {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm<CreateFormData>();
  const { mutate: createClass, isPending } = useCreateClass();

  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  }

  function onSubmit(data: CreateFormData) {
    createClass(data.name, {
      onSuccess: async (response) => {
        const courseId = response?.class?.id;

        // Upload image if selected
        if (imageFile && courseId) {
          try {
            await uploadCourseImage(courseId, imageFile);
          } catch {
            toast.error("Course created but image upload failed.");
          }
        }

        toast.success("Course created successfully!");
        navigate(`/classes/${courseId}/home`);
      },
      onError: (err) => {
        toast.error(err instanceof Error ? err.message : "Failed to create course.");
      },
    });
  }

  return (
    <div className="p-4 md:p-8 w-full max-w-260 mx-auto flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-text-primary m-0">Create Course</h2>
      </div>

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
                {imagePreview ? (
                  <img
                    src={imagePreview}
                    alt="Course cover preview"
                    className="w-full h-full object-cover"
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
              placeholder="e.g. COSC 404 Advanced Database Systems"
              disabled={isPending}
              className="px-3.5 py-2.5 border border-border rounded-lg bg-bg-secondary text-text-primary text-sm font-[inherit] w-full focus:outline-none focus:ring-2 focus:ring-btn-primary/30 focus:border-btn-primary transition-all disabled:opacity-60"
              {...register("name", { required: "Course name is required" })}
            />
            {errors.name && (
              <span className="text-xs text-red-500">{errors.name.message}</span>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-4 border-t border-border">
            <button
              type="button"
              onClick={() => navigate(-1)}
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
              {isPending ? "Creating..." : "Create course"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
