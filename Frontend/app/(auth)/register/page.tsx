"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowserClient } from "@/lib/supabaseClient";
import { toast } from "react-toastify";
import { Eye, EyeOff } from "lucide-react";
import Image from "next/image";

export default function RegisterPage() {
  const router = useRouter();
  const supabase = createSupabaseBrowserClient();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const getPasswordStrength = () => {
    if (password.length < 6) return "Weak";
    if (password.length >= 6 && password.length < 8) return "Medium";
    if (
      password.length >= 8 &&
      /[A-Z]/.test(password) &&
      /[0-9]/.test(password)
    )
      return "Strong";
    return "Medium";
  };

  const strength = getPasswordStrength();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setLoading(true);

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          first_name: firstName,
          last_name: lastName,
        },
      },
    });

    setLoading(false);

    if (error) {
      toast.error(error.message);
      return;
    }

    toast.success("Verification email sent. Please check inbox.");
    router.push("/login");
  };

  return (
    <div className="bg-gray-100 flex items-center justify-center px-6 py-1">
  <div className="w-full sm:w-[600px] md:w-[550px] lg:w-[500px] bg-white rounded-xl shadow-md p-6">

        {/* Logo */}
        <div className="flex justify-center mb-2">
          <Image
            src="/sinewave-logo.png"
            alt="Sinewave Logo"
            width={190}
            height={50}
          />
        </div>

        <h2 className="text-2xl font-bold text-center text-[#737d8c] mb-3 tracking-wide">
          Create Account
        </h2>

        <form onSubmit={handleRegister} className="space-y-1">

        
          {/* First Name */}
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              First Name
            </label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-black placeholder-gray-400 focus:ring-2 focus:ring-[#2a7fc9] focus:outline-none"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
          </div>

          {/* Last Name */}
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Last Name
            </label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-black placeholder-gray-400 focus:ring-2 focus:ring-[#2a7fc9] focus:outline-none"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Email
            </label>
            <input
              type="email"
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-black placeholder-gray-400 focus:ring-2 focus:ring-[#2a7fc9] focus:outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                className="w-full border border-gray-300 rounded-md px-3 py-1.5 pr-10 text-black placeholder-gray-400 focus:ring-2 focus:ring-[#2a7fc9] focus:outline-none"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <span
                className="absolute right-3 top-2.5 cursor-pointer text-gray-600"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </span>
            </div>
          </div>

          {/* Strength Indicator */}
          {password && (
            <p
              className={`text-sm ${
                strength === "Weak"
                  ? "text-red-500"
                  : strength === "Medium"
                  ? "text-yellow-600"
                  : "text-green-600"
              }`}
            >
              Strength: {strength}
            </p>
          )}

          {/* Confirm Password */}
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                className="w-full border border-gray-300 rounded-md px-3 py-1.5 pr-10 text-black placeholder-gray-400 focus:ring-2 focus:ring-[#2a7fc9] focus:outline-none"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
              <span
                className="absolute right-3 top-2.5 cursor-pointer text-gray-600"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </span>
            </div>
          </div>

          {confirmPassword && password !== confirmPassword && (
            <p className="text-sm text-red-500">
              Passwords do not match
            </p>
          )}

          {/* Button */}
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
            {loading ? "Creating..." : "Register"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600 mt-6">
          Already have an account?{" "}
          <span
            onClick={() => router.push("/login")}
            className="text-[#2a7fc9] cursor-pointer hover:underline"
          >
            Login
          </span>
        </p>
      </div>
    </div>
  );
}