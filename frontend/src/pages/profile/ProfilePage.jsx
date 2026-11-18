import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { authService } from "../../services/authService";
import { getErrorMessage } from "../../services/api";
import { ErrorBanner, PageHeader } from "../../components/common/UIPrimitives";

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [jobTitle, setJobTitle] = useState(user?.job_title || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await authService.updateProfile({
        first_name: firstName,
        last_name: lastName,
        job_title: jobTitle,
        phone,
      });
      await refreshUser();
      setMessage("Profile updated successfully.");
    } catch (err) {
      setError(getErrorMessage(err, "Failed to update profile."));
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await authService.changePassword({ old_password: oldPassword, new_password: newPassword });
      setOldPassword("");
      setNewPassword("");
      setMessage("Password changed successfully.");
    } catch (err) {
      setError(getErrorMessage(err, "Failed to update password."));
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader title="My Profile" subtitle={`${user?.email} • Role: ${user?.role}`} />

      <ErrorBanner message={error} onDismiss={() => setError("")} />
      {message && (
        <div className="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50 text-sm text-emerald-800">{message}</div>
      )}

      <form onSubmit={handleProfileSave} className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-slate-900">Personal Details</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">First Name</label>
            <input value={firstName} onChange={(e) => setFirstName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Last Name</label>
            <input value={lastName} onChange={(e) => setLastName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Job Title</label>
            <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Phone</label>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
        </div>
        <button type="submit" className="px-4 py-2 rounded-lg bg-blue-700 text-white text-sm font-semibold hover:bg-blue-800">
          Save Profile
        </button>
      </form>

      <form onSubmit={handlePasswordChange} className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-slate-900">Change Password</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Current Password</label>
            <input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" required />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">New Password (min 10 chars)</label>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" required minLength={10} />
          </div>
        </div>
        <button type="submit" className="px-4 py-2 rounded-lg bg-navy-800 text-white text-sm font-semibold hover:bg-navy-900">
          Update Password
        </button>
      </form>
    </div>
  );
}
