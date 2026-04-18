import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Textbox from '../../ui/Textbox';
import toast from 'react-hot-toast';
import { changeRequiredPassword } from '../../services/userApi';
import { useAuth } from './AuthProvider';
import { pageClasses, blockClasses, innerClasses, inputsClasses, inputChunkClasses } from './LoginForm';

export default function ChangePassword() {
  const navigate = useNavigate();
  const { refreshAuth } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isPending, setIsPending] = useState(false);

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('All fields are required');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('New password must be at least 6 characters');
      return;
    }

    setIsPending(true);
    try {
      await changeRequiredPassword(currentPassword, newPassword);

      const stored = localStorage.getItem('user');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          parsed.must_change_password = false;
          localStorage.setItem('user', JSON.stringify(parsed));
        } catch {
          // Ignore malformed local storage payloads.
        }
      }

      await refreshAuth();
      toast.success('Password changed successfully! Redirecting...');
      setTimeout(() => navigate('/home'), 2000);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to change password');
      setIsPending(false);
    }
  };

  return (
    <div className={pageClasses}>
      <div className={blockClasses}>
        <div className="text-center w-full">
          <img src="/oc_logo.png" alt="OC Logo" className="w-14 h-14 mx-auto mb-3 object-contain" />
          <h1 className="text-2xl font-bold text-text-primary m-0">Change Password</h1>
          <p className="text-text-secondary text-sm mt-1">You must change your temporary password before continuing.</p>
        </div>

        <div className={innerClasses}>
          <div className={inputsClasses}>
            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Current Password</label>
              <Textbox type='password' placeholder='••••••••' onInput={setCurrentPassword} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">New Password</label>
              <Textbox type='password' placeholder='••••••••' onInput={setNewPassword} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Confirm New Password</label>
              <Textbox type='password' placeholder='••••••••' onInput={setConfirmPassword} />
            </div>
          </div>
        </div>

        <button
          onClick={handleChangePassword}
          disabled={isPending}
          className="w-full px-5 py-2.5 rounded-lg bg-btn-primary text-white text-sm font-semibold hover:brightness-110 active:scale-[0.98] transition-all cursor-pointer border-none disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isPending ? 'Changing...' : 'Change Password'}
        </button>
      </div>
    </div>
  );
}
