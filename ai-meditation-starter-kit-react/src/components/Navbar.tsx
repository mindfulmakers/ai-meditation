import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const navigate = useNavigate();

  const handleLogin = () => {
    navigate("/login");
  };

  const handleSignup = () => {
    navigate("/signup");
  };

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled ? "bg-white/95 backdrop-blur-sm shadow-sm" : "bg-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-4">
          <div className="flex items-center">
            <a href="#" className="flex items-center">
              Logo
            </a>
          </div>

          <nav className="hidden md:flex items-center space-x-6">
            <a
              href="#features"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Features
            </a>
            <a
              href="#pricing"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Pricing
            </a>
            <a
              href="#about"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              About
            </a>
            <a
              href="#contact"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Contact
            </a>
            <Button
              variant="ghost"
              className="text-gray-600 hover:text-gray-900"
              onClick={handleLogin}
            >
              Log in
            </Button>
            <Button
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={handleSignup}
            >
              Sign up
            </Button>
          </nav>

          <button
            className="md:hidden focus:outline-none"
            onClick={() => setIsOpen(!isOpen)}
            aria-expanded={isOpen}
            aria-label="Toggle menu"
          >
            {isOpen ? (
              <X className="h-6 w-6 text-gray-700" />
            ) : (
              <Menu className="h-6 w-6 text-gray-700" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <div
        className={`md:hidden ${isOpen ? "block" : "hidden"} bg-white border-t`}
      >
        <div className="px-4 py-4 space-y-4">
          <a
            href="#features"
            className="block text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => setIsOpen(false)}
          >
            Features
          </a>
          <a
            href="#pricing"
            className="block text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => setIsOpen(false)}
          >
            Pricing
          </a>
          <a
            href="#about"
            className="block text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => setIsOpen(false)}
          >
            About
          </a>
          <a
            href="#contact"
            className="block text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => setIsOpen(false)}
          >
            Contact
          </a>
          <div className="pt-4 flex flex-col space-y-2">
            <Button
              variant="ghost"
              className="w-full justify-center text-gray-600 hover:text-gray-900"
              onClick={handleLogin}
            >
              Log in
            </Button>
            <Button
              className="w-full justify-center bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={handleSignup}
            >
              Sign up
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
