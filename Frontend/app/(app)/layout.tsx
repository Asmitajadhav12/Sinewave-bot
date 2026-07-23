import { TopNavigation } from "@/components/TopNavigation";

export const metadata = {
  title: "Sinewave Support",
  description: "Converted from React",
  
  icons: {
    icon: "/assets/Sinewave_logo (1).png",
    
  },
};

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white">
      <TopNavigation userName="Admin" />
      <main>{children}</main>
    </div>
  );
}
