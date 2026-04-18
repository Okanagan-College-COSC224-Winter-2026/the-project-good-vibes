import { useState } from 'react';
import Textbox from '../../ui/Textbox';
import Button from '../../ui/Button';
import { tryRegister } from '../../util/api';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { pageClasses, blockClasses, innerClasses, inputsClasses, inputChunkClasses } from './LoginForm';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();

  const attemptRegister = async () => {
    if (!name || !email || !password || !confirmPassword) {
      toast.error('All fields are required');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    try {
      if (await tryRegister(name, email, password)) {
        toast.success('Account created! Please sign in.');
        navigate('/');
      }
    } catch {
      toast.error('Failed to create account');
    }
  }

  return (
    <div className={pageClasses}>
      <div className={blockClasses}>
        <div className="text-center w-full">
          <img src="/oc_logo.png" alt="OC Logo" className="w-14 h-14 mx-auto mb-3 object-contain" />
          <h1 className="text-2xl font-bold text-text-primary m-0">Create an account</h1>
          <p className="text-text-secondary text-sm mt-1">Sign up to get started</p>
        </div>

        <div className={innerClasses}>
          <div className={inputsClasses}>
            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Full Name</label>
              <Textbox placeholder='John Doe' onInput={setName} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Email</label>
              <Textbox type='email' placeholder='you@example.com' onInput={setEmail} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Password</label>
              <Textbox type='password' placeholder='••••••••' onInput={setPassword} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Confirm Password</label>
              <Textbox type='password' placeholder='••••••••' onInput={setConfirmPassword} />
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <Button onClick={() => attemptRegister()} children="Create Account" />
          <Button onClick={() => navigate('/')} type='secondary' children="Back to Sign In" />
        </div>
      </div>
    </div>
  );
}
