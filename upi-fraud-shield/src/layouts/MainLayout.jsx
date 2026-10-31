import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

export const MainLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-canvas font-sans text-ink">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      <div className="min-h-screen lg:pl-64 flex flex-col min-w-0">
        <Navbar onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)} />
        <main className="flex-1 w-full max-w-[1600px] mx-auto px-4 py-6 sm:px-6 lg:px-8 lg:py-8 animate-fade-in">
          <Outlet />
        </main>
        <footer className="border-t border-outline-soft bg-white px-4 py-4 text-center text-xs text-slate-500 sm:px-6">
          Local heuristic prototype · Synthetic records · No NPCI or payment-provider connection
        </footer>
      </div>
    </div>
  );
};

export default MainLayout;
