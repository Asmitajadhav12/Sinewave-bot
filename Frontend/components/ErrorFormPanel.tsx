"use client";
import Image from "next/image";
import { useState, useEffect } from "react";
import { X, Trash2, Upload } from "lucide-react";

import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Card } from "./ui/card";
import { callApi } from "@/utils/apiUtils";
import { toast } from "react-toastify";

/* ================= TYPES ================= */

interface Screenshot {
  id: number;
  screenshot_url: string;
}

export interface ErrorFormData {
  functionAreaId: number | null;
  description: string;
  solutionSteps: string;
  screenshots: File[];
}

interface FunctionArea {
  id: number;
  title: string;
}

interface ErrorFormPanelProps {
  isOpen: boolean;
  onClose: () => void;
  mode?: "add" | "view" | "edit";
  productId: number;
  productTitle: string; // ✅ ADDED
  errorData?: any | null;
}

/* ================= COMPONENT ================= */

export function ErrorFormPanel({
  isOpen,
  onClose,
  mode = "add",
  productId,
  productTitle, // ✅ ADDED
  errorData,
}: ErrorFormPanelProps) {
  const isViewMode = mode === "view";

  const [formData, setFormData] = useState<ErrorFormData>({
    functionAreaId: null,
    description: "",
    solutionSteps: "",
    screenshots: [],
  });

  const [functionAreas, setFunctionAreas] = useState<FunctionArea[]>([]);
  const [existingScreenshots, setExistingScreenshots] = useState<Screenshot[]>([]);
  const [screenshotsToDelete, setScreenshotsToDelete] = useState<number[]>([]);
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  /* ================= FETCH FUNCTION AREAS ================= */

  useEffect(() => {
    fetch("/api/functionAreas")
      .then((res) => res.json())
      .then(setFunctionAreas)
      .catch(() => setFunctionAreas([]));
  }, []);

  /* ================= PREFILL ================= */

  useEffect(() => {
    if (!errorData || functionAreas.length === 0) {
      setExistingScreenshots(errorData?.screenshots ?? []);
      return;
    }

    setFormData({
      functionAreaId:
        errorData.functionAreaId !== undefined
          ? Number(errorData.functionAreaId)
          : null,
      description: errorData.description ?? "",
      solutionSteps: errorData.solution ?? "",
      screenshots: [],
    });

    setExistingScreenshots(errorData.screenshots ?? []);
    setScreenshotsToDelete([]);
  }, [errorData, functionAreas]);

  /* ================= BREADCRUMB LABEL ================= */

  const actionLabel =
    mode === "view"
      ? "View Error"
      : mode === "edit"
      ? "Edit Error"
      : "Add Error";

  /* ================= DELETE ================= */

  const deleteScreenshot = (id: number) => {
    setScreenshotsToDelete((prev) => [...prev, id]);
    setExistingScreenshots((prev) => prev.filter((s) => s.id !== id));
  };

  // ------------------- ADD CAN SUBMIT HERE -------------------
  const canSubmit =
    formData.functionAreaId !== null &&
    formData.description.trim() !== "" &&
    formData.solutionSteps.trim() !== "";

  /* ================= SUBMIT ================= */

  const addNewErrorInfo = async () => {
    try {
      const fd = new FormData();
      fd.append(
        "errorInfo",
        JSON.stringify({
          description: formData.description,
          solution: formData.solutionSteps,
          functionAreaId: formData.functionAreaId,
          productId,
          productTitle,
        })
      );

      if (formData.screenshots.length > 0) {
        formData.screenshots.forEach((file) => {
          fd.append("screenshots", file);
        });
      }

      const res = await callApi("/api/errorInfo", {
        method: "POST",
        body: fd,
      });

      toast.success("Error added successfully");
      return String(res.id);
    } catch (error) {
      toast.error("Failed to add error");
    }
  };

  const updateErrorInfo = async (errorId: string) => {
    try {
      const fd = new FormData();
      fd.append(
        "errorInfo",
        JSON.stringify({
          errorId,
          description: formData.description,
          solution: formData.solutionSteps,
          functionAreaId: formData.functionAreaId,
          productId,
          productTitle,
        })
      );

      if (screenshotsToDelete.length > 0) {
        fd.append(
          "screenshotsToDelete",
          JSON.stringify(screenshotsToDelete)
        );
      }

      if (formData.screenshots.length > 0) {
        formData.screenshots.forEach((file) => {
          fd.append("screenshots", file);
        });
      }

      await callApi("/api/errorInfo", {
        method: "PUT",
        body: fd,
      });

      toast.success("Error updated successfully");
    } catch (error) {
      toast.error("Failed to update error");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isViewMode) return;

    if (mode === "add") {
      await addNewErrorInfo();
    } else if (mode === "edit") {
      if (!errorData?.id) return;
      await updateErrorInfo(String(errorData.id));
    }

    setFormData((prev) => ({ ...prev, screenshots: [] }));
    setScreenshotsToDelete([]);
    onClose();
  };

  if (!isOpen) return null;

  const labelStyle = "text-[#005bac] font-bold text-sm mb-2 block";
  const inputStyle =
    "bg-white text-black rounded-lg px-4 py-2 w-full outline-none disabled:text-black disabled:opacity-100";

  const shadowStyle: React.CSSProperties = {
    boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
  };

  return (
    <>
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      <div
        className="fixed right-0 top-0 z-50 h-full w-[100%] bg-[#EAF7FD] shadow-2xl overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <Card className="h-full rounded-none border-0 pt-2 px-6 pb-6 bg-transparent">

          {/* ✅ BREADCRUMB ADDED */}
          <div className="w-full px-2 py-2 mb-2 flex items-center gap-2 text-sm">
            <span className="text-gray-500">Products</span>
            <span className="text-gray-400 text-lg">›</span>
            <span className="text-[#005bac] font-medium">
              {productTitle}
            </span>
            <span className="text-gray-400 text-lg">›</span>
            <span className="text-gray-800 font-semibold">
              {actionLabel}
            </span>
          </div>

          <div className="flex justify-between items-center mb-0">
            <h2 className="font-bold text-[#005bac] text-lg">
              {mode === "view"
                ? "Error Details"
                : mode === "edit"
                ? "Edit Error"
                : "Add New Error"}
            </h2>

            <Button onClick={onClose} className="bg-white border">
              <X className="h-4 w-4" />
            </Button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Function Area */}
            <div>
              <Label className={labelStyle}>Function Area *</Label>
              <Select
                value={formData.functionAreaId?.toString()}
                onValueChange={(value) =>
                  setFormData({
                    ...formData,
                    functionAreaId: Number(value),
                  })
                }
                disabled={isViewMode}
              >
                <SelectTrigger className={inputStyle} style={shadowStyle}>
                  <SelectValue placeholder="Select function area" />
                </SelectTrigger>
                <SelectContent className="bg-white text-black">
                  {functionAreas.map((fa) => (
                    <SelectItem key={fa.id} value={fa.id.toString()}>
                      {fa.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Description */}
            <div>
              <Label className={labelStyle}>Description *</Label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                disabled={isViewMode}
                className={`${inputStyle} max-h-[60px] min-h-[60px] overflow-y-auto resize-none`}
                style={shadowStyle}
              />
            </div>

            {/* Solution */}
            <div>
              <Label className={labelStyle}>Solution Steps *</Label>
              <Textarea
                value={formData.solutionSteps}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    solutionSteps: e.target.value,
                  })
                }
                disabled={isViewMode}
                className={`${inputStyle} max-h-[100px] min-h-[85px] overflow-y-auto resize-none`}
                style={shadowStyle}
              />
            </div>

            {/* Screenshot View Mode */}
            {isViewMode && existingScreenshots.length > 0 && (
              <div>
                <Label className={labelStyle}>Screenshots</Label>
                <div className="grid grid-cols-2 gap-3 max-h-[150px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-[#00A3E0]/40 scrollbar-track-transparent">
                  {existingScreenshots.map((img) => (
                    <div key={`screenshot-${img.id}`} className="relative w-[500px] h-[100px]">
                      <Image
                        key={img.id}
                        src={`/api/image/${encodeURIComponent(img.screenshot_url)}`}
                        alt={img.screenshot_url}
                        fill
                        onClick={() =>
                          setPreviewImage(`/api/image/${encodeURIComponent(img.screenshot_url)}`)
                        }
                        className="w-full h-[120px] object-cover rounded-md border bg-white cursor-pointer"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Section */}
            {!isViewMode && (
              <div>
                <Label className={labelStyle}>Upload Screenshot</Label>

                <div className="grid grid-cols-[400px_1fr] gap-4 mt-2">
                  <div>
                    <input
                      type="file"
                      id="screenshotUpload"
                      multiple
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const newFiles = Array.from(e.target.files || []);
                        setFormData((prev) => ({
                          ...prev,
                          screenshots: [...prev.screenshots, ...newFiles],
                        }));
                      }}
                    />

                    <label
                      htmlFor="screenshotUpload"
                      className="flex flex-col items-center justify-center cursor-pointer rounded-xl border-2 border-dashed border-[#00A3E0] bg-white w-[320px] h-[170px] hover:bg-[#EAF7FD] transition"
                    >
                      <Upload className="h-5 w-5 text-[#00A3E0]" />
                      <span className="text-sm font-medium text-[#00A3E0] text-center px-1">
                        Click to Upload
                      </span>
                      <span className="text-xs text-gray-500">
                        JPG, PNG supported
                      </span>
                    </label>
                  </div>

                  <div className="grid grid-cols-2 gap-3 max-h-[180px] overflow-y-auto pr-2">
                    {existingScreenshots.map((img) => (
                      <div
                        key={`existing-${img.id}`}
                        className="relative w-full aspect-video cursor-pointer group"
                        onClick={() =>
                          setPreviewImage(`/api/image/${encodeURIComponent(img.screenshot_url)}`)
                        }
                      >
                        <Image
                          src={`/api/image/${encodeURIComponent(img.screenshot_url)}`}
                          alt="existing"
                          fill
                          className="object-cover rounded-md border bg-white group-hover:opacity-80 transition"
                        />

                        {mode === "edit" && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteScreenshot(img.id);
                            }}
                            className="absolute top-2 right-2 transition-all duration-300 ease-in-out hover:scale-110 cursor-pointer"
                          >
                            <Trash2
                              size={18}
                              className="text-black transition-colors duration-300 ease-in-out hover:text-red-600"
                            />
                          </button>
                        )}
                      </div>
                    ))}

                    {formData.screenshots.map((file, idx) => (
                      <div
                        key={`new-${idx}`}
                        className="relative w-full aspect-video cursor-pointer group"
                        onClick={() =>
                          setPreviewImage(URL.createObjectURL(file))
                        }
                      >
                        <Image
                          src={URL.createObjectURL(file)}
                          alt="preview"
                          fill
                          className="object-cover rounded-md border bg-white group-hover:opacity-80 transition"
                        />

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFormData((prev) => ({
                              ...prev,
                              screenshots: prev.screenshots.filter((_, i) => i !== idx),
                            }));
                          }}
                          className="absolute top-3 right-3 transition-all duration-300 ease-in-out hover:scale-110 cursor-pointer"
                        >
                          <Trash2
                            size={18}
                            className="text-black transition-colors duration-300 ease-in-out hover:text-red-600"
                          />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {!isViewMode && (
              <div className="sticky bottom-0 bg-[#EAF7FD] pt-3 pb-4 flex gap-3">
                <Button
                  type="submit"
                  className="bg-[#00a6e6] text-white px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={!canSubmit}
                >
                  {mode === "edit" ? "Update" : "Submit"}
                </Button>

                <Button
                  type="button"
                  onClick={onClose}
                  className="bg-white border"
                >
                  Cancel
                </Button>
              </div>
            )}
          </form>
        </Card>
      </div>

      {previewImage && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[100]">
          <div className="relative max-w-4xl w-full h-[80vh]">
            <Image
              src={previewImage}
              alt="Preview"
              fill
              className="object-contain rounded-lg"
            />

            <button
              onClick={() => setPreviewImage(null)}
              className="absolute top-30 right-1 bg-black/60 hover:bg-black rounded-full p-2 cursor-pointer"
            >
              <X className="h-4 w-4 text-white" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}