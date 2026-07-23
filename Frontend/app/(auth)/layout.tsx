export const metadata = {
  title: "Sinewave Support",
  description: "Converted from React",
  icons: {
    icon: "/assets/Sinewave_logo%20(1).png",
  },
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      {children}
    </div>
  );
}