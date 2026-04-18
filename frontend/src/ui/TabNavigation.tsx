import { Link } from "react-router-dom"

interface Props {
  tabs: {
    label: string,
    path: string,
  }[]
}

export default function TabNavigation(props: Props) {
  return (
    <div className="TabNav flex flex-row justify-start items-center w-full px-4 border-b border-border bg-bg-primary overflow-x-auto">
      {props.tabs.map(tab => {
        const isActive = tab.path === window.location.pathname
        return (
          <Link
            key={tab.path}
            className={`flex flex-row justify-center items-center py-3 px-4 text-sm font-medium border-b-2 cursor-pointer transition-colors duration-150 -mb-px whitespace-nowrap ${
              isActive
                ? 'border-btn-primary text-btn-primary'
                : 'border-transparent text-text-secondary hover:text-text-primary hover:border-bg-tertiary'
            }`}
            to={tab.path}
          >
            {tab.label}
          </Link>
        )
      })}
    </div>
  )
}
