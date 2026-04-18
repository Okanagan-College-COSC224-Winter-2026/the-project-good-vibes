import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Textbox from '../../ui/Textbox';
import Button from '../../ui/Button';
import toast from 'react-hot-toast';
import { tryLogin } from '../../util/api';
import { useAuth } from './AuthProvider';

// Shared layout classes for auth pages (Login, Register, ChangePassword, CreateTeacher)
export const pageClasses = "flex flex-col items-center justify-center min-h-screen w-full bg-gradient-to-br from-slate-50 via-white to-slate-100 p-4"
export const blockClasses = "flex flex-col items-center w-full sm:max-w-md bg-white rounded-2xl shadow-lg border border-border p-8 gap-6"
export const innerClasses = "w-full"
export const inputsClasses = "flex flex-col w-full gap-4"
export const inputChunkClasses = "flex flex-col gap-1.5 w-full"

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const attemptLogin = async () => {
    try {
      const result = await tryLogin(email, password);
      if (result) {
        login(Boolean(result.must_change_password));
        if (result.must_change_password) {
          navigate('/change-password');
        } else {
          navigate('/home');
        }
      } else {
        toast.error('Invalid email or password');
      }
    } catch {
      toast.error('Invalid email or password');
    }
  }

  return (
    <div className={pageClasses}>
      <div className={blockClasses}>
        <div className="text-center w-full">
          <img src="/oc_logo.png" alt="OC Logo" className="w-14 h-14 mx-auto mb-3 object-contain" />
          <h1 className="text-2xl font-bold text-text-primary m-0">Welcome back</h1>
          <p className="text-text-secondary text-sm mt-1">Sign in to your account</p>
        </div>

        <div className={innerClasses}>
          <div className={inputsClasses}>
            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Email</label>
              <Textbox placeholder='you@example.com' onInput={setEmail} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Password</label>
              <Textbox type='password' placeholder='••••••••' onInput={setPassword} />
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <Button onClick={() => attemptLogin()} children="Sign In" />
          <Button onClick={() => navigate('/register')} type='secondary' children="Create account" />
        </div>
      </div>
    </div>
  );
}
