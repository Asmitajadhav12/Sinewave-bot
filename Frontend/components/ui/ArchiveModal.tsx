"use client";

import { X, RotateCcw } from "lucide-react";

interface ErrorData {
  id: string;
  description: string;
  solution: string;
  functionArea: string;
  archived: boolean;
}

interface ArchiveModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: ErrorData[];
  onUnarchive: (id: string) => void;
}

export function ArchiveModal({
  isOpen,
  onClose,
  data,
  onUnarchive,
}: ArchiveModalProps) {
  if (!isOpen) return null;

  const archivedErrors = data.filter((err) => err.archived);

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/40 z-40" />

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-6">
        <div className="bg-white w-full max-w-5xl rounded-2xl shadow-xl overflow-hidden">

          {/* Header */}
          <div className="flex justify-between items-center px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-[#0099CC]">
              Archived Errors
            </h2>

            <button onClick={onClose}>
              <X className="w-5 h-5 text-gray-600 hover:text-black" />
            </button>
          </div>

          {/* Table */}
          <div className="max-h-[500px] overflow-y-auto">
            {archivedErrors.length === 0 ? (
              <div className="p-10 text-center text-gray-400">
                No archived errors
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-[#f6f9fc]">
                  <tr>
                    <th className="text-left px-6 py-3 font-medium text-gray-700">
                      Title
                    </th>
                    <th className="text-left px-6 py-3 font-medium text-gray-700">
                      Description
                    </th>
                    <th className="text-left px-6 py-3 font-medium text-gray-700">
                      Function Area
                    </th>
                    <th className="text-center px-6 py-3 font-medium text-gray-700">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {archivedErrors.map((error, index) => (
                    <tr
                      key={error.id}
                      className={`${
                        index % 2 === 0
                          ? "bg-white"
                          : "bg-gray-50/40"
                      } border-b`}
                    >
                      <td className="px-6 py-4">
                        {error.description}
                      </td>

                      <td className="px-6 py-4 text-gray-600">
                        {error.solution}
                      </td>

                      <td className="px-6 py-4">
                        <span className="px-3 py-1 rounded-full text-xs border border-blue-200 bg-white text-[#1D4ED8]">
                          {error.functionArea}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => onUnarchive(error.id)}
                          className="flex items-center gap-2 mx-auto text-sm bg-[#00A3E0] text-white px-3 py-1.5 rounded-md hover:bg-[#5ec5e6] transition"
                        >
                          <RotateCcw size={14} />
                          Unarchive
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </>
  );
}