import toast from "react-hot-toast";
import { importStudentsForCourse } from "./api";

export const importCSV = (id: string | number) => {
  const input = document.createElement("input");
  input.setAttribute("type", "file");
  input.setAttribute("accept", ".csv");

  input.addEventListener("change", async () => {
    const file = input.files?.[0];

    if (!file) {
      toast.error("Please select a file to upload");
      return;
    }

    const reader = new FileReader();

    reader.onload = async () => {
      const text = reader.result?.toString();

      if (!text) {
        toast.error("Please select a valid CSV file");
        return;
      }

      try {
        const result = await importStudentsForCourse(Number(id), text);
        toast.success(result.msg || "Students added successfully!");
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Failed to import students");
      }
    };

    reader.readAsText(file);
  });

  input.click();
};
