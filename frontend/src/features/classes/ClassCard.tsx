import { Link } from "react-router-dom"

interface Props {
  image: string
  name: string
  subtitle: string
  href: string
  grade?: string
  onClick?: () => void
}

export default function ClassCard(props: Props) {
  return (
    <Link
      to={props.href}
      className="w-full flex flex-col rounded-xl overflow-hidden select-none cursor-pointer bg-white border border-border shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
      onClick={props.onClick}
    >
      <img
        src={props.image}
        alt={props.name}
        className="w-full h-44 object-cover"
      />
      <div className="w-full p-4 flex flex-col gap-1.5 flex-1">
        <h2
          className="text-text-primary text-lg font-semibold overflow-hidden [display:-webkit-box] [-webkit-line-clamp:2] [-webkit-box-orient:vertical] leading-snug max-h-[3.4rem] break-words m-0"
        >
          {props.name}
        </h2>
        <div className="mt-auto flex flex-col gap-1.5">
          <p className="text-text-secondary text-sm whitespace-nowrap overflow-hidden text-ellipsis m-0">
            {props.subtitle}
          </p>
          {props.grade && (
            <span className="text-text-tertiary text-xs font-medium bg-gray-100 py-1 px-2 rounded-full self-start">
              {props.grade}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
