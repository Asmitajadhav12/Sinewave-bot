"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { toast } from "react-toastify";
import { createSupabaseBrowserClient } from "@/lib/supabaseClient";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const supabase = createSupabaseBrowserClient();

      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        toast.error(error.message);
        return;
      }

      toast.success("Login successful");
      router.push("/");
    } catch (err) {
      console.error("Login error:", err);
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl p-8 border border-gray-200">

        {/* Logo */}
        <div className="flex flex-col items-center mb-2">
          <Image
            src="/sinewave-logo.png"
            alt="Sinewave Computer Services"
            width={190}
            height={50}
            className="object-contain"
            priority
          />

          <h2 className="text-2xl font-semibold text-[#737d8c] mt-4"> 
            Login
          </h2>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">

          {/* Email */}
          <div>
            <label className="block mb-2 font-medium text-black">
              Email
            </label>
            <input
              type="email"
              placeholder="Enter your email"
              className="w-full px-4 py-3 rounded-lg border border-gray-300 text-black placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2a7fc9]"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {/* Password */}
          <div>
            <label className="block mb-2 font-medium text-black">
              Password
            </label>

            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 text-black placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2a7fc9] pr-16"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-gray-500 hover:text-gray-700"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {/* Login Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full 
    bg-[#2a7fc9] 
    text-white 
    py-2.5 
    rounded-md 
    mt-3
    cursor-pointer
    hover:bg-[#0099cc]
    active:bg-[#0077a3]
    transition-all 
    duration-200 
    disabled:opacity-50 
    disabled:cursor-not-allowed"
          >
            {loading ? "Logging in..." : "Login"}
          </button>

          {/* Forgot Password */}
          <div className="text-center">
            <button
              type="button"
              className="text-sm text-[#2a7fc9] hover:underline"
            >
              Forgot password?
            </button>
          </div>

          {/* Sign Up Link */}
          <p className="text-center text-sm text-gray-600 mt-4">
            Don’t have an account?{" "}
            <Link
              href="/register"
              className="text-[#2a7fc9] font-medium hover:underline"
            >
              Sign up
            </Link>
          </p>

        </form>
      </div>
    </div>
  );
}