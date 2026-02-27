import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { logout, useFullUser } from "openbase-react-shared";
import { useNavigate } from "react-router-dom";
const UserProfile = () => {
  const navigate = useNavigate();
  const { user, isLoading } = useFullUser();

  // Get initials for avatar fallback
  const getInitials = () => {
    if (!user) return "T";
    return user.first_name.charAt(0);
  };
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="relative h-10 w-10 rounded-full p-0 ml-4"
        >
          <Avatar>
            {/* You could add a real image here if the API provided one */}
            <AvatarFallback>{isLoading ? "..." : getInitials()}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={12} className="w-56">
        <DropdownMenuLabel>
          {isLoading ? (
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">Loading user data...</p>
            </div>
          ) : (
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-gray-500 font-light">{user?.email}</p>
            </div>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate("/dashboard/settings")}>
          Account Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout}>Log out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
export default UserProfile;
