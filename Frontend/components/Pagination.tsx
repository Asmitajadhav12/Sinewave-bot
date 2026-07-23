import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./ui/button";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
}: PaginationProps) {
  const startItem =
    totalItems === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1;

  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];

    if (totalPages <= 1) return pages;

    pages.push(1);

    const left = currentPage - 1;
    const right = currentPage + 1;

    if (left > 2) {
      pages.push("...");
    }

    for (
      let i = Math.max(2, left);
      i <= Math.min(totalPages - 1, right);
      i++
    ) {
      pages.push(i);
    }

    if (right < totalPages - 1) {
      pages.push("...");
    }

    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div
      className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 px-6 py-4 border-t bg-white"
      style={{ borderColor: "#E5E7EB" }}
    >
      {/* Range Info */}
      <div
        style={{
          color: "#4B5563",
          fontFamily: "Poppins",
          fontSize: "0.875rem",
        }}
      >
        Showing{" "}
        <span style={{ fontWeight: 500 }}>
          {startItem}–{endItem}
        </span>{" "}
        of{" "}
        <span style={{ fontWeight: 500 }}>
          {totalItems}
        </span>{" "}
        results
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 flex-wrap">

        {/* Previous */}
        <Button
          variant="outline"
          size="sm"
          aria-label="Go to previous page"
          disabled={currentPage === 1}
          onClick={() =>
            currentPage > 1 && onPageChange(currentPage - 1)
          }
          className="gap-1 transition-all duration-200"
          style={{
            borderColor: "#E5E7EB",
            fontFamily: "Poppins",
            fontWeight: 500,
            opacity: currentPage === 1 ? 0.5 : 1,
          }}
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>

        {/* Page Numbers */}
        <div className="flex gap-1 flex-wrap">
          {getPageNumbers().map((page, index) =>
            page === "..." ? (
              <span
                key={`ellipsis-${index}`}
                className="px-3 py-1 text-sm"
                style={{
                  color: "#9CA3AF",
                  fontFamily: "Poppins",
                }}
              >
                ...
              </span>
            ) : (
              <Button
                key={page}
                size="sm"
                aria-label={`Go to page ${page}`}
                aria-current={
                  currentPage === page ? "page" : undefined
                }
                onClick={() => onPageChange(page as number)}
                className="transition-all duration-200"
                style={{
                  backgroundColor:
                    currentPage === page
                      ? "#00A3E0"
                      : "#FFFFFF",
                  color:
                    currentPage === page
                      ? "#FFFFFF"
                      : "#4B5563",
                  borderColor:
                    currentPage === page
                      ? "#00A3E0"
                      : "#E5E7EB",
                  borderWidth: "1px",
                  borderStyle: "solid",
                  borderRadius: "6px",
                  fontFamily: "Poppins",
                  fontWeight:
                    currentPage === page ? 500 : 400,
                }}
                onMouseEnter={(e) => {
                  if (currentPage !== page) {
                    e.currentTarget.style.backgroundColor =
                      "#EAF7FD";
                    e.currentTarget.style.borderColor =
                      "#00A3E0";
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentPage !== page) {
                    e.currentTarget.style.backgroundColor =
                      "#FFFFFF";
                    e.currentTarget.style.borderColor =
                      "#E5E7EB";
                  }
                }}
              >
                {page}
              </Button>
            )
          )}
        </div>

        {/* Next */}
        <Button
          variant="outline"
          size="sm"
          aria-label="Go to next page"
          disabled={currentPage === totalPages}
          onClick={() =>
            currentPage < totalPages &&
            onPageChange(currentPage + 1)
          }
          className="gap-1 transition-all duration-200"
          style={{
            borderColor: "#E5E7EB",
            fontFamily: "Poppins",
            fontWeight: 500,
            opacity:
              currentPage === totalPages ? 0.5 : 1,
          }}
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>

      </div>
    </div>
  );
}
