interface Props {
  children?: React.ReactNode
  className?: string
}

export default function AssignmentCard(props: Props) {
  return (
    <div
      className={`flex flex-row justify-start items-center text-text-primary w-full h-auto font-semibold text-sm text-left gap-2 ${props.className ?? ''}`}
    >
      <img src="/icons/document.svg" alt="document" className="w-9 h-9 flex-shrink-0" />
      <span>{props.children}</span>
    </div>
  )
}
