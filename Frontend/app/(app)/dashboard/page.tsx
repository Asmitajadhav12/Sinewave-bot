"use client";

import { useEffect, useState, useCallback } from "react";
import { toast, Toaster } from "sonner";
import { Plus, Search, RefreshCw, Filter } from "lucide-react";

import { ErrorTable } from "@/components/ErrorTable";
import { ErrorFormPanel } from "@/components/ErrorFormPanel";
import { Product, ProductSidebar } from "@/components/ProductSidebar";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Pagination } from "@/components/Pagination";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

import { callApi } from "@/utils/apiUtils";

/* ================= TYPES ================= */

export interface ErrorData {
  id: string;
  description: string;
  solution: string;
  functionArea: string;
  functionAreaId: number;
  archived: boolean;
  productId: number;
  screenshots: any[];
  totalReported: number;
  resolvedCount: number;
  notResolvedCount: number;
}

interface FunctionArea {
  id: number;
  title: string;
}

/* ================= PAGE ================= */

export default function Page() {
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [selectedProductTitle, setSelectedProductTitle] = useState("");

  const [errors, setErrors] = useState<ErrorData[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [functionAreas, setFunctionAreas] = useState<FunctionArea[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [globalLoading, setGlobalLoading] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFunctionAreas, setSelectedFunctionAreas] = useState<string[]>([]);
  const [showArchived, setShowArchived] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState<"add" | "edit" | "view">("add");
  const [activeError, setActiveError] = useState<ErrorData | null>(null);

  /* ================= FETCHERS ================= */

  const fetchProducts = async () => {
    try {
      setGlobalLoading(true);
      const res = await callApi("/api/products");
      setProducts(res || []);
      setSelectedProductId(res?.[0]?.id || null);
      setSelectedProductTitle(res?.[0]?.name || "");
    } catch {
      toast.error("Failed to load products");
    } finally {
      setGlobalLoading(false);
    }
  };

  const fetchErrors = useCallback(async () => {
    if (!selectedProductId) return;

    try {
      setIsLoading(true);
      setGlobalLoading(true);

      const res = await callApi(
        `/api/errorInfo?productId=${selectedProductId}`
      );

      const cleaned = (res || []).map((item: ErrorData) => ({
        ...item,
        functionArea: item.functionArea?.trim() || "",
      }));

      setErrors(cleaned);
    } catch {
      toast.error("Failed to load errors");
    } finally {
      setIsLoading(false);
      setGlobalLoading(false);
    }
  }, [selectedProductId]);

  const fetchFunctionAreas = async () => {
    try {
      setGlobalLoading(true);
      const res = await callApi("/api/functionAreas");
      if (Array.isArray(res)) {
        setFunctionAreas(res);
      }
    } catch {
      toast.error("Failed to load function areas");
    } finally {
      setGlobalLoading(false);
    }
  };

  useEffect(() => {
    fetchFunctionAreas();
    fetchProducts();
  }, []);

  useEffect(() => {
    fetchErrors();
  }, [fetchErrors]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedFunctionAreas, showArchived]);

  /* ================= ARCHIVE ================= */

  const handleArchive = async (id: string, currentArchived: boolean) => {
    try {
      setGlobalLoading(true);

      await callApi("/api/errorInfo", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id,
          archived: !currentArchived,
        }),
      });

      setErrors((prev) =>
        prev.map((e) =>
          e.id === id ? { ...e, archived: !currentArchived } : e
        )
      );

      toast.success(
        currentArchived
          ? "Unarchived successfully"
          : "Archived successfully"
      );
    } catch {
      toast.error("Failed to update archive status");
    } finally {
      setGlobalLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      setGlobalLoading(true);

      await callApi(`/api/errorInfo?id=${id}`, { method: "DELETE" });

      setErrors((prev) => prev.filter((e) => e.id !== id));
      toast.success("Error deleted successfully");
    } catch {
      toast.error("Failed to delete error");
    } finally {
      setGlobalLoading(false);
    }
  };

  /* ================= FILTER ================= */

  const filteredErrors = errors
    .filter((e) =>
      `${e.description} ${e.solution}`
        .toLowerCase()
        .includes(searchQuery.toLowerCase())
    )
    .filter(
      (e) =>
        selectedFunctionAreas.length === 0 ||
        selectedFunctionAreas.includes(e.functionArea)
    );

  const displayData = showArchived
    ? filteredErrors.filter((e) => e.archived)
    : filteredErrors.filter((e) => !e.archived);

  const totalPages = Math.ceil(displayData.length / itemsPerPage);

  const paginatedData = displayData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  /* ================= UI ================= */

  return (
    <div className="bg-white min-h-screen relative">
      <Toaster position="top-right" richColors />

      <div className="flex">
        <ProductSidebar
          products={products}
          selectedProductId={selectedProductId}
          onProductSelect={(productId) => {
            setSelectedProductId(productId);
            const product = products.find((p) => p.id === productId);
            setSelectedProductTitle(product?.name || "");
          }}
        />

        {selectedProductId && (
          <div className="flex-1 p-6">
            <div className="w-full bg-white border-b border-gray-200 px-6 py-1 mb-3 text-sm flex items-center gap-2">
              <span className="text-gray-500">Products</span>
              <span className="text-gray-400">›</span>
              <span className="text-[#005bac] font-medium">
                {selectedProductTitle || "Product"}
              </span>
              <span className="text-gray-400">›</span>
              <span className="text-gray-700 font-semibold">
                Dashboard
              </span>
            </div>

            <h1 className="text-2xl font-bold text-[#005bac] mb-3">
              Error Dashboard
            </h1>

            <div className="flex flex-wrap gap-2 mb-4 items-center">
              <div className="relative w-96">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#00A3E0]" />
                <Input
                  className="h-9 pl-9 pr-3 w-full border border-gray-300 focus:outline-none focus:border-[#00A3E0] focus:ring-2 focus:ring-[#00A3E0]/40 transition-all duration-300 ease-in-out"
                  placeholder="Search error..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    className="bg-white border border-gray-300 text-black"
                  >
                    <Filter className="h-4 w-4 mr-2 text-[#00A3E0]" />
                    Function Area
                  </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent className="w-72 max-h-[400px] bg-white border border-gray-200 shadow-md rounded-md">
                  <DropdownMenuLabel className="text-black font-semibold">
                    Select Function Area
                  </DropdownMenuLabel>

                  <DropdownMenuSeparator />

                  {functionAreas.map((area) => (
                    <DropdownMenuItem
                      key={area.id}
                      onSelect={(e) => e.preventDefault()}
                      className="flex items-center gap-2 text-black hover:bg-gray-100 focus:bg-gray-100 cursor-pointer"
                    >
                      <Checkbox
                        checked={selectedFunctionAreas.includes(area.title)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedFunctionAreas((prev) => [
                              ...prev,
                              area.title,
                            ]);
                          } else {
                            setSelectedFunctionAreas((prev) =>
                              prev.filter((a) => a !== area.title)
                            );
                          }
                        }}
                      />
                      <span className="text-black">{area.title}</span>
                    </DropdownMenuItem>
                  ))}

                  <DropdownMenuSeparator />

                  <div className="p-2">
                    <button
                      onClick={() => setSelectedFunctionAreas([])}
                      className="w-full py-1 text-sm font-medium text-black border border-[#00b7f4] rounded-md hover:bg-[#e6f7fe] transition duration-200 cursor-pointer"
                    >
                      Clear All
                    </button>
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                variant="outline"
                onClick={() => setShowArchived((p) => !p)}
              >
                {showArchived ? "Show Active" : "Show Archived"}
              </Button>

              <Button
                variant="outline"
                onClick={fetchErrors}
                disabled={isLoading}
              >
                <RefreshCw
                  className={`h-4 w-4 mr-2 ${
                    isLoading ? "animate-spin" : ""
                  }`}
                />
                Refresh
              </Button>

              <Button
                className="bg-[#00A3E0] !text-white font-semibold hover:bg-[#00bdfc]"
                onClick={() => {
                  setActiveError(null);
                  setPanelMode("add");
                  setPanelOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-1 !text-white" />
                Add Error
              </Button>
            </div>

            {isLoading ? (
              <LoadingSpinner />
            ) : (
              <>
                <ErrorTable
                  data={paginatedData}
                  onView={(id) => {
                    const e = errors.find((x) => x.id === id);
                    if (!e) return;
                    setActiveError(e);
                    setPanelMode("view");
                    setPanelOpen(true);
                  }}
                  onEdit={(id) => {
                    const e = errors.find((x) => x.id === id);
                    if (!e) return;
                    setActiveError(e);
                    setPanelMode("edit");
                    setPanelOpen(true);
                  }}
                  onArchive={(id) => {
                    const e = errors.find((x) => x.id === id);
                    if (!e) return;
                    handleArchive(id, e.archived);
                  }}
                  onDelete={handleDelete}
                />

                {totalPages > 1 && (
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    totalItems={displayData.length}
                    itemsPerPage={itemsPerPage}
                    onPageChange={setCurrentPage}
                  />
                )}
              </>
            )}
          </div>
        )}
      </div>

      {globalLoading && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-gray-500/40 backdrop-blur-sm">
          <div className="h-12 w-12 border-4 border-white border-t-[#00b7f4] rounded-full animate-spin"></div>
        </div>
      )}

      {panelOpen && selectedProductId && (
        <ErrorFormPanel
          isOpen={panelOpen}
          onClose={() => {
            setPanelOpen(false);
            fetchErrors();
          }}
          mode={panelMode}
          errorData={activeError}
          productId={selectedProductId}
          productTitle={selectedProductTitle}
        />
      )}
    </div>
  );
}