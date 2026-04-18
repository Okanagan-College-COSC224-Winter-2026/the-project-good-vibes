import { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface SidebarNavLinkProps {
  to: string
  icon: ReactNode
  children: ReactNode
  active?: boolean
}

export default function SidebarNavLink({ to, icon, children, active }: SidebarNavLinkProps) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium no-underline transition-colors duration-150 ${
        active
          ? 'bg-btn-primary/10 text-btn-primary'
          : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
      }`}
    >
      <span className={`flex-shrink-0 ${active ? 'text-btn-primary' : 'text-text-secondary group-hover:text-text-primary'}`}>
        {icon}
      </span>
      {children}
    </Link>
  )
}
