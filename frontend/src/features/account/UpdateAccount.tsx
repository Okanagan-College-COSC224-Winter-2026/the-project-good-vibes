import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { useUser, useUpdateProfile, useUploadAvatar, useChangePassword, useDeleteAccount, getUserAvatarUrl } from './useUser'
import { getUserId, logout } from '../../util/login'
import Modal from '../../ui/Modal'

interface UserProfile {
  id: number
  name: string
  email: string
  role: string
  avatar_url: string | null
}

export default function Profile() {
  const { data: profile } = useUser() as { data: UserProfile | undefined }
  const updateProfileMutation = useUpdateProfile()
  const uploadAvatarMutation = useUploadAvatar()
  const changePasswordMutation = useChangePassword()
  const deleteAccountMutation = useDeleteAccount()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [profileLoading, setProfileLoading] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [pwLoading, setPwLoading] = useState(false)

  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteLoading, setDeleteLoading] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const userId = getUserId()

  useEffect(() => {
    if (profile) {
      setName(profile.name ?? '')
      setEmail(profile.email ?? '')
    }
  }, [profile])

  const handleAvatarSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarFile(file)
    setAvatarPreview(URL.createObjectURL(file))
  }

  const handleProfileUpdate = async () => {
    setProfileLoading(true)
    try {
      if (avatarFile) {
        await uploadAvatarMutation.mutateAsync(avatarFile)
        setAvatarFile(null)
      }

      const payload: { name?: string; email?: string } = {}
      if (name !== profile?.name) payload.name = name
      if (email !== profile?.email) payload.email = email

      if (Object.keys(payload).length > 0) {
        await updateProfileMutation.mutateAsync(payload)
      }

      toast.success('Account updated successfully.')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update account.')
    } finally {
      setProfileLoading(false)
    }
  }

  const handleProfileCancel = () => {
    setName(profile?.name ?? '')
    setEmail(profile?.email ?? '')
    setAvatarFile(null)
    setAvatarPreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handlePasswordUpdate = async () => {
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match.')
      return
    }
    setPwLoading(true)
    try {
      await changePasswordMutation.mutateAsync({ currentPassword, newPassword })
      toast.success('Password updated successfully.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update password.')
    } finally {
      setPwLoading(false)
    }
  }

  const handlePasswordCancel = () => {
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
  }

  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      toast.error('Please enter your password.')
      return
    }
    setDeleteLoading(true)
    try {
      await deleteAccountMutation.mutateAsync(deletePassword)
      toast.success('Account deleted.')
      logout()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete account.')
    } finally {
      setDeleteLoading(false)
    }
  }

  const closeDeleteModal = () => {
    setDeleteModalOpen(false)
    setDeletePassword('')
  }

  const inputClass =
    'px-3 py-2.5 border border-border rounded-lg bg-bg-secondary text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-btn-primary focus:border-btn-primary transition-colors w-full'

  const currentAvatarSrc =
    avatarPreview ??
    (profile?.avatar_url ? `http://localhost:5000${profile.avatar_url}` : null) ??
    (userId ? getUserAvatarUrl(userId) : null)

  return (
    <div className="p-6 md:p-8 w-full max-w-260 mx-auto">
      <h1 className="text-2xl font-bold text-text-primary mb-1">Update your account</h1>
      <p className="text-text-secondary text-sm mb-6">Manage your profile and credentials</p>

      {/* Section 1: Update user data */}
      <section className="bg-white rounded-2xl border border-border shadow-sm mb-6 overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-base font-semibold text-text-primary m-0">Update user data</h2>
        </div>

        <div className="px-6 py-5 flex flex-col gap-5">
          {/* Avatar */}
          <div className="flex items-center gap-5">
            <div className="w-20 h-20 rounded-full bg-bg-secondary flex items-center justify-center overflow-hidden border border-border flex-shrink-0">
              {currentAvatarSrc ? (
                <img
                  src={currentAvatarSrc}
                  alt="Avatar"
                  className="w-full h-full object-cover"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                />
              ) : (
                <span className="text-2xl font-bold text-text-secondary select-none">
                  {profile?.name?.charAt(0).toUpperCase() ?? '?'}
                </span>
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-text-primary mb-1.5 m-0">Profile photo</p>
              <label className="cursor-pointer">
                <span className="inline-flex items-center px-3 py-1.5 rounded-lg border border-border text-sm text-text-secondary hover:bg-bg-secondary transition-colors">
                  {avatarFile ? avatarFile.name : 'Choose photo'}
                </span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/gif,image/webp"
                  className="hidden"
                  onChange={handleAvatarSelect}
                />
              </label>
              {avatarFile && (
                <button
                  className="ml-2 text-xs text-text-secondary hover:text-red-600 bg-transparent border-none cursor-pointer"
                  onClick={() => {
                    setAvatarFile(null)
                    setAvatarPreview(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                >
                  Remove
                </button>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary">Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className={inputClass}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary">Full name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your full name"
              className={inputClass}
            />
          </div>

          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={handleProfileCancel}
              disabled={profileLoading}
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleProfileUpdate}
              disabled={profileLoading}
              className="px-4 py-2 rounded-lg bg-btn-primary text-white text-sm font-semibold hover:brightness-110 transition-all cursor-pointer border-none disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {profileLoading ? 'Saving…' : 'Update account'}
            </button>
          </div>
        </div>
      </section>

      {/* Section 2: Update password */}
      <section className="bg-white rounded-2xl border border-border shadow-sm mb-6 overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-base font-semibold text-text-primary m-0">Update password</h2>
        </div>

        <div className="px-6 py-5 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary">Current password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary">New password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary">Confirm password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={handlePasswordCancel}
              disabled={pwLoading}
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handlePasswordUpdate}
              disabled={pwLoading}
              className="px-4 py-2 rounded-lg bg-btn-primary text-white text-sm font-semibold hover:brightness-110 transition-all cursor-pointer border-none disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {pwLoading ? 'Saving…' : 'Update password'}
            </button>
          </div>
        </div>
      </section>

      {/* Section 3: Danger Zone */}
      <section className="bg-white rounded-2xl border border-red-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-red-200 bg-red-50/50">
          <h2 className="text-base font-semibold text-red-700 m-0">Danger Zone</h2>
        </div>
        <div className="px-6 py-5 flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-text-primary m-0 mb-0.5">Delete your account</p>
              <p className="text-xs text-text-secondary m-0">Permanently remove your account and all associated data. This action cannot be undone.</p>
            </div>
            <button
              onClick={() => setDeleteModalOpen(true)}
              className="flex-shrink-0 px-4 py-2 rounded-lg border border-red-300 text-sm font-medium text-red-600 hover:bg-red-600 hover:text-white transition-colors cursor-pointer bg-transparent"
            >
              Delete account
            </button>
          </div>
        </div>
      </section>

      {/* Delete Account Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={closeDeleteModal}
        title="Delete Account"
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm text-text-secondary m-0">
            This will permanently delete your account and all your data. Please enter your password to confirm.
          </p>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-text-primary">Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              className={inputClass}
            />
          </div>
          <div className="flex gap-3 justify-end pt-2 border-t border-border">
            <button
              onClick={closeDeleteModal}
              disabled={deleteLoading}
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors cursor-pointer bg-transparent disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleDeleteAccount}
              disabled={deleteLoading || !deletePassword}
              className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors cursor-pointer border-none disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {deleteLoading ? 'Deleting…' : 'Delete my account'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
