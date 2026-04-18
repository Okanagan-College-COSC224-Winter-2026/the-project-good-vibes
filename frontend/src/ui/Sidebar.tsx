import { useLocation } from 'react-router-dom'
import SidebarNavLink from '../ui/SidebarNavLink'
import { logout } from '../util/login'

function HomeIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
    </svg>
  )
}

function UserCircleIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  )
}

function ArrowRightOnRectangleIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 9V5.25A2.25 2.25 0 0 1 10.5 3h6a2.25 2.25 0 0 1 2.25 2.25v13.5A2.25 2.25 0 0 1 16.5 21h-6a2.25 2.25 0 0 1-2.25-2.25V15m-3 0-3-3m0 0 3-3m-3 3H15" />
    </svg>
  )
}

export default function Sidebar() {
  const { pathname } = useLocation()

  return (
    <aside className="hidden md:flex w-64 min-w-64 h-screen bg-white border-r border-border flex-col sticky top-0 z-30">
      {/* Brand */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-border flex-shrink-0">
        <img src="/oc_logo.png" alt="OC Logo" className="w-9 h-9 object-contain flex-shrink-0" />
        <div>
          <p className="text-text-primary font-bold text-sm leading-tight m-0">Peer Review</p>
          <p className="text-text-secondary text-xs m-0">Dashboard</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col flex-1 px-3 py-4 gap-0.5 overflow-y-auto">
        <SidebarNavLink to="/home" icon={<HomeIcon />} active={pathname === '/home'}>
          Home
        </SidebarNavLink>

        <SidebarNavLink to="/profile/1" icon={<UserCircleIcon />} active={pathname.includes('/profile')}>
          My Account
        </SidebarNavLink>
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-border flex-shrink-0">
        <button
          onClick={() => logout()}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-text-secondary transition-colors duration-150 hover:bg-red-50 hover:text-red-600 cursor-pointer border-none bg-transparent"
        >
          <ArrowRightOnRectangleIcon />
          Log out
        </button>
      </div>
    </aside>
  )
}
