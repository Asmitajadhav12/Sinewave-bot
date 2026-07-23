"use client";

import { LogOut, ArrowLeft } from "lucide-react";
import Image from "next/image";
import { Button } from "./ui/button";
import { callApi } from "@/utils/apiUtils";

interface TopNavigationProps {
  userName: string;
  productName?: string;
  onBackToProducts?: () => void;
}

export function TopNavigation({
  userName,
  productName,
  onBackToProducts,
}: TopNavigationProps) {

  const handleLogout = async () => {
    await callApi("/api/auth/logout", {
      method: "POST",
    });

    window.location.href = "/login";
  };

  return (
    <header
      className="w-full shadow-md sticky top-0 z-40"
      style={{
        backgroundColor: "#FFFFFF",
        borderBottom: "1px solid #E5E7EB",
      }}
    >
      <div className="px-8 py-3">
        <div className="flex items-center justify-between">

          {/* Left: Logo */}
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              
              {/* ✅ Clean Logo */}
              <Image
                src="/sinewave-logo.png"
                alt="Sinewave Computer Services"
                width={180}
                height={48}
                className="object-contain"
                priority
                unoptimized
              />

              {productName && (
                <h1
                  className="text-lg mt-2"
                  style={{
                    color: "#0099CC",
                    fontFamily: "Poppins",
                    fontWeight: 600,
                  }}
                >
                  Error Resolution Dashboard
                </h1>
              )}
            </div>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-3">
            {productName && onBackToProducts && (
              <Button
                variant="outline"
                className="gap-2 h-9 px-4"
                onClick={onBackToProducts}
                style={{
                  borderColor: "#E5E7EB",
                  backgroundColor: "#FFFFFF",
                  color: "#0099CC",
                  fontFamily: "Poppins",
                  fontWeight: 500,
                }}
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Products
              </Button>
            )}

            {/* Admin badge */}
            <Button
              variant="outline"
              className="gap-2 h-9 px-4"
              disabled
              style={{
                borderColor: "#E5E7EB",
                backgroundColor: "#ffffff",
                color: "#1F2937",
                fontFamily: "Poppins sans-serif",
                fontWeight: 500,
              }}
            >
              <div className="w-6 h-6 bg-[#0099CC] rounded-full flex items-center justify-center">
                <span
                  className="text-xs"
                  style={{
                    color: "#FFFFFF",
                    fontFamily: "Poppins",
                    fontWeight: 600,
                  }}
                >
                  {userName.charAt(0)}
                </span>
              </div>
              <span>{userName}</span>
            </Button>

            {/* Logout */}
            <Button
          className="bg-[#00A3E0] !text-white font-semibold hover:bg-[#00bdfc]"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4 mr-1 !text-white" />
          Logout
        </Button>
          </div>
        </div>
      </div>

      <style>{`
        input::placeholder {
          color: #6B7280 !important;
        }
        input {
          color: #1F2937 !important;
          border: 1px solid #E5E7EB !important;
        }
        select {
          color: #1F2937 !important;
          border: 1px solid #E5E7EB !important;
          background-color: #FFFFFF !important;
        }
        select option {
          color: #1F2937 !important;
          background-color: #FFFFFF !important;
        }
        button {
          color: #1F2937 !important;
        }
        label {
          color: #1F2937 !important;
        }
        [role="button"] {
          color: #1F2937 !important;
        }
        button[class*="Filter"] {
          background-color: #FFFFFF !important;
          border: 1px solid #E5E7EB !important;
          color: #0099CC !important;
        }
        button[class*="Add"] {
          background-color: #0099CC !important;
          border: 1px solid #0099CC !important;
          color: #FFFFFF !important;
        }
      `}</style>
    </header>
  );
}
