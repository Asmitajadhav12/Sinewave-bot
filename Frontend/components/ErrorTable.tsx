"use client";

import { Eye, Pencil, Trash2, Archive } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { useMemo, useState } from "react";


/* ================= TYPES ================= */

export interface ErrorData {
  id: string;
  description: string;
  solution: string;
  functionArea: string;
  archived: boolean;
  totalReported: number;
  resolvedCount: number;
  notResolvedCount: number;
}

interface ErrorTableProps {
  data: ErrorData[];
  onView: (id: string) => void;
  onEdit: (id: string) => void;
  onArchive: (id: string) => void;
  onDelete: (id: string) => void;
}

/* ================= CONSTANTS ================= */

const ROWS_PER_PAGE = 7;

/* ================= COMPONENT ================= */

export function ErrorTable({
  data,
  onView,
  onEdit,
  onArchive,
  onDelete,
}: ErrorTableProps) {
  const [page, setPage] = useState(1);

  const totalPages = Math.ceil(data.length / ROWS_PER_PAGE);

  const paginatedData = useMemo(() => {
    const start = (page - 1) * ROWS_PER_PAGE;
    return data.slice(start, start + ROWS_PER_PAGE);
  }, [data, page]);

  /* -------- FIRST SENTENCE FUNCTION -------- */
  const getFirstSentence = (text: string) => {
    if (!text) return "";

    const match = text.match(/.*?[.!?](\s|$)/);
    if (match) {
      const first = match[0].trim();
      return first.length < text.length ? `${first}...` : first;
    }

    return text.length > 90 ? `${text.slice(0, 90)}...` : text;
  };

  return (
    <div className="bg-white rounded-2xl shadow-md shadow-gray-200/60 overflow-hidden w-full flex flex-col">

      {/* Scrollable Table Area */}
      <div className="h-[420px] overflow-y-auto overflow-x-hidden">

        <Table className="w-full table-fixed">

          {/* HEADER */}
          <TableHeader className="bg-[#daf5fe] sticky top-0 z-10">
            <TableRow className="border-b border-gray-200">

              <TableHead className="w-[30%] text-gray-800 font-semibold text-sm py-3 pl-6">
                Error Description
              </TableHead>

              <TableHead className="w-[30%] text-gray-800 font-semibold text-sm py-3">
                Error Solution
              </TableHead>

              <TableHead className="w-[20%] text-gray-800 font-semibold text-sm py-3">
                Function Area
              </TableHead>

              <TableHead className="w-[20%] text-gray-800 font-semibold text-sm py-3">
                Error Stats
              </TableHead>


              <TableHead className="w-[20%] text-gray-800 font-semibold text-sm py-3 text-center">
                Actions
              </TableHead>

            </TableRow>
          </TableHeader>

          {/* BODY */}
          <TableBody>
            {paginatedData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="py-20 text-center text-gray-400">
                  No errors found
                </TableCell>
              </TableRow>
            ) : (
              paginatedData.map((error, index) => (
                <TableRow
                  key={error.id}
                  className={`${
                    index % 2 === 0 ? "bg-white" : "bg-gray-50/40"
                  } hover:bg-blue-50 transition`}
                >
                  {/* ERROR DESCRIPTION */}
                  <TableCell className="align-top py-3 border-b border-gray-100 w-[30%] relative">
                  <div className="group relative cursor-pointer">
                    
                    {/* Ellipsis Text */}
                    <p className="text-gray-600 text-sm leading-6 truncate">
                      {error.description}
                    </p>

                    {/* Popup Window */}
                    <div className="absolute left-0 top-8 z-50 hidden group-hover:block bg-white shadow-xl rounded-lg p-4 w-80 border border-gray-200">
                      <p className="text-sm text-gray-700 leading-6 whitespace-normal">
                        {error.description}
                      </p>
                    </div>

                  </div>
                </TableCell>




                  {/* ERROR SOLUTION */}
                  <TableCell className="align-top py-3 border-b border-gray-100 w-[30%] relative">
                  <div className="group relative cursor-pointer">
                    
                    {/* Ellipsis Text */}
                    <p className="text-gray-600 text-sm leading-6 truncate">
                      {error.solution}
                    </p>

                    {/* Popup Window */}
                    <div className="absolute left-0 top-8 z-50 hidden group-hover:block bg-white shadow-xl rounded-lg p-4 w-80 border border-gray-200">
                      <p className="text-sm text-gray-700 leading-6 whitespace-normal">
                        {error.solution}
                      </p>
                    </div>

                  </div>
                </TableCell>

                  {/* FUNCTION AREA */}
                  <TableCell className="align-top py-3 border-b border-gray-100">
                  {error.functionArea ? (
                    <span
                      className="inline-flex px-3 py-1 rounded-full 
                                bg-white text-[#008cbb] text-sm font-medium 
                                border border-blue-200 shadow-sm break-words"
                    >
                      {error.functionArea}
                    </span>
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </TableCell>
                  
                  {/* ERROR STATS */}
                  <TableCell className="align-top py-3 border-b border-gray-100">
                    <div className="text-sm text-gray-700 leading-5">
                      <div>Reported: {error.totalReported ?? 0}</div>
                      <div className="text-green-600">
                        Resolved: {error.resolvedCount ?? 0}
                      </div>
                      <div className="text-red-500">
                        Not Resolved: {error.notResolvedCount ?? 0}
                      </div>
                    </div>
                  </TableCell>


                  {/* ACTIONS */}
                  <TableCell className="align-top py-3 border-b border-gray-100">
                    <div className="flex items-center justify-center gap-3 flex-wrap">
                      <Eye
                        size={16}
                        className="text-green-800 cursor-pointer hover:scale-110 transition"
                        onClick={() => onView(error.id)}
                      />
                      <Pencil
                        size={16}
                        className="text-blue-500 cursor-pointer hover:scale-110 transition"
                        onClick={() => onEdit(error.id)}
                      />
                      <Archive
                        size={16}
                        className="text-orange-400 cursor-pointer hover:scale-110 transition"
                        onClick={() => onArchive(error.id)}
                      />
                      <Trash2
                        size={16}
                        className="text-red-500 cursor-pointer hover:scale-110 transition"
                        onClick={() => onDelete(error.id)}
                      />
                    </div>
                  </TableCell>

                </TableRow>
              ))
            )}
          </TableBody>

        </Table>
      </div>

      {/* PAGINATION */}
      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 px-6 py-3 bg-[#daf5fe]">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1 rounded-md text-sm border border-gray-300 text-gray-600
                       hover:bg-gray-100 transition disabled:opacity-40"
          >
            Prev
          </button>

          {[...Array(totalPages)].map((_, i) => (
            <button
              key={i}
              onClick={() => setPage(i + 1)}
              className={`px-3 py-1 rounded-md text-sm transition ${
                page === i + 1
                  ? "bg-[#00b7f4] text-white shadow-sm"
                  : "border border-gray-300 text-gray-600 hover:bg-[#00b7f4] hover:text-white"
              }`}
            >
              {i + 1}
            </button>
          ))}

          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1 rounded-md text-sm border border-gray-300 text-gray-600
                       hover:bg-gray-100 transition disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}