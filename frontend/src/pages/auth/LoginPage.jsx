import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { LifeBuoy, Lock, Mail } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../services/api";
import { loginSchema } from "../../validations/schemas";
import { ErrorBanner } from "../../components/common/UIPrimitives";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (values) => {
    setServerError("");
    try {
      await login(values.email, values.password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setServerError(getErrorMessage(err, "Invalid email or password."));
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      <div className="hidden lg:flex lg:w-1/2 bg-navy-900 text-white p-12 flex-col justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center">
            <LifeBuoy className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="text-xl font-bold tracking-tight">HelpDesk</div>
            <div className="text-xs text-slate-400">Enterprise IT Service Management</div>
          </div>
        </div>

        <div className="max-w-md">
          <h1 className="text-3xl font-bold leading-tight">
            Centralized IT Incident Tracking, SLA Governance & AI Triage.
          </h1>
          <p className="mt-4 text-slate-300 text-sm leading-relaxed">
            Report technical issues, coordinate engineering queues, enforce priority-based response
            SLAs, and resolve incidents faster with knowledge base and Gemini-assisted diagnostics.
          </p>
        </div>

        <div className="text-xs text-slate-400">
          Role-Based Access Control • MySQL 8 ACID Persistence • Automated SLA Monitoring
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-sm p-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Sign in to HelpDesk</h2>
            <p className="text-sm text-slate-500 mt-1">Enter your corporate email and password.</p>
          </div>

          <ErrorBanner message={serverError} onDismiss={() => setServerError("")} />

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  {...register("email")}
                  placeholder="name@company.com"
                  className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>
              {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  {...register("password")}
                  placeholder="••••••••••"
                  className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
              </div>
              {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 px-4 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold transition-colors disabled:opacity-60"
            >
              {isSubmitting ? "Signing in..." : "Sign In"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
