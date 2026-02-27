import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import {
  FormErrors,
  ProviderList,
  useConfig,
  useLogin,
  WebAuthnLoginButton,
} from "openbase-react-shared";
import { Link, useNavigate } from "react-router-dom";

export default function Login() {
  const {
    email,
    setEmail,
    password,
    setPassword,
    handleSubmit,
    isLoading,
    errors,
  } = useLogin();
  const config = useConfig();
  const navigate = useNavigate();
  const { toast } = useToast();
  const hasProviders = config?.data?.socialaccount?.providers?.length > 0;

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      toast({
        title: "Missing information",
        description: "Please provide both email and password.",
        variant: "destructive",
      });
      return;
    }

    handleSubmit();
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-gradient-to-b from-white to-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
          <h1 className="text-2xl font-light text-center mb-8 text-gray-900">
            Log in
          </h1>

          <FormErrors errors={errors} />

          <form onSubmit={onSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                disabled={isLoading}
                className="border-gray-200 focus-visible:ring-gray-400"
              />
              <FormErrors param="email" errors={errors} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                disabled={isLoading}
                className="border-gray-200 focus-visible:ring-gray-400"
              />
              <FormErrors param="password" errors={errors} />
              <div className="flex justify-end mt-1">
                <Link
                  to="/account/password/reset"
                  className="text-sm hover:text-primary transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800"
            >
              {isLoading ? "Logging in..." : "Log in"}
            </Button>
          </form>

          {config?.data?.account?.login_by_code_enabled && (
            <div className="mt-4">
              <Button variant="outline" className="w-full" asChild>
                <Link to="/account/login/code">Send me a sign-in code</Link>
              </Button>
            </div>
          )}

          <div className="mt-4">
            <Button variant="outline" className="w-full" asChild>
              <WebAuthnLoginButton>Sign in with a passkey</WebAuthnLoginButton>
            </Button>
          </div>

          {hasProviders && (
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-gray-500">
                    Or continue with
                  </span>
                </div>
              </div>
              <div className="mt-4">
                <ProviderList callbackURL="/account/provider/callback" />
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 text-center space-y-2">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <Link
              to="/account/signup"
              className="font-medium transition-colors"
            >
              Sign up
            </Link>
          </p>
          <Button
            variant="ghost"
            onClick={() => navigate("/")}
            className="text-gray-600 hover:text-gray-800"
          >
            Back to Home
          </Button>
        </div>
      </div>
    </div>
  );
}
