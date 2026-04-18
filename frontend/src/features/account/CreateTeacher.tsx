import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Textbox from '../../ui/Textbox';
import toast from 'react-hot-toast';
import { createTeacherAccount } from '../../util/api';
import { pageClasses, blockClasses, innerClasses, inputsClasses, inputChunkClasses } from '../authentication/LoginForm';

export default function CreateTeacher() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isPending, setIsPending] = useState(false);

  const handleCreateTeacher = async () => {
    if (!name || !email || !password) {
      toast.error('All fields are required');
      return;
    }

    if (password.length < 6) {
      toast.error('Temporary password must be at least 6 characters');
      return;
    }

    setIsPending(true);
    try {
      const result = await createTeacherAccount(name, email, password);
      toast.success(`Teacher account created for ${result.user.name}`);
      setName('');
      setEmail('');
      setPassword('');
    } catch {
      toast.error('Failed to create teacher account');
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div className={pageClasses}>
      <div className={blockClasses}>
        <div className="text-center w-full">
          <h1 className="text-2xl font-bold text-text-primary m-0">Create Teacher Account</h1>
          <p className="text-text-secondary text-sm mt-1">Set up a new teacher with a temporary password.</p>
        </div>

        <div className={innerClasses}>
          <div className={inputsClasses}>
            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Teacher Name</label>
              <Textbox placeholder='Full name...' onInput={setName} value={name} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Institutional Email</label>
              <Textbox type='email' placeholder='teacher@institution.edu' onInput={setEmail} value={email} />
            </div>

            <div className={inputChunkClasses}>
              <label className="text-sm font-medium text-text-primary">Temporary Password</label>
              <Textbox type='password' placeholder='••••••••' onInput={setPassword} value={password} />
            </div>
          </div>
        </div>

        <p className="text-xs text-text-secondary m-0 text-center">The teacher will be prompted to change their password on first login.</p>

        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <button
            onClick={handleCreateTeacher}
            disabled={isPending}
            className="flex-1 px-5 py-2.5 rounded-lg bg-btn-primary text-white text-sm font-semibold hover:brightness-110 active:scale-[0.98] transition-all cursor-pointer border-none disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isPending ? 'Creating...' : 'Create Teacher'}
          </button>
          <button
            onClick={() => navigate('/home')}
            className="flex-1 px-5 py-2.5 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
