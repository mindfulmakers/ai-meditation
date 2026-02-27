import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar";
import UserProfile from "@/components/UserProfile";
import { Clipboard, Home, PieChart } from "lucide-react";
import { useFullUser } from "openbase-react-shared";
import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

interface ExampleDashboardLayoutProps {
  children: React.ReactNode;
}

const ExampleDashboardLayout: React.FC<ExampleDashboardLayoutProps> = ({
  children,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isLoading } = useFullUser();

  // Navigation items with their respective paths, icons, and titles
  const navItems = [
    {
      path: "/dashboard",
      icon: Home,
      title: "Dashboard 1",
    },
    {
      path: "/dashboard/two",
      icon: PieChart,
      title: "Dashboard 2",
    },
    {
      path: "/dashboard/three",
      icon: Clipboard,
      title: "Dashboard 3",
    },
  ];

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-gray-50">
        <Sidebar>
          <SidebarHeader className="p-4 border-b">
            <div className="flex items-center justify-start py-2">
              <h1 className="text-xl font-bold text-gray-900">My App</h1>
            </div>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Dashboard</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navItems.map((item) => (
                    <SidebarMenuItem key={item.path}>
                      <SidebarMenuButton
                        isActive={location.pathname === item.path}
                        onClick={() => navigate(item.path)}
                        tooltip={item.title}
                      >
                        <item.icon />
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>

        <div className="flex-1 overflow-auto">
          <header className="bg-white shadow-sm border-b h-16 flex items-center px-6 sticky top-0 z-10">
            <div className="flex-1 flex justify-between items-center">
              <h2 className="text-xl text-gray-900 font-sans">
                {isLoading
                  ? "Loading..."
                  : `Welcome back, ${user?.first_name || "User"}`}
              </h2>
              <div className="flex items-center space-x-1">
                <UserProfile />
              </div>
            </div>
          </header>
          <main className="w-full p-6">{children}</main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default ExampleDashboardLayout;
