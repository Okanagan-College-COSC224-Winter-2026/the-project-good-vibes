interface Props {
  onClick?: () => void
  children?: React.ReactNode
  type?: 'regular' | 'secondary'
  disabled?: boolean
}

export default function Button(props: Props) {
  const base = 'inline-flex items-center justify-center appearance-none border-none rounded-lg px-4 py-2.5 font-semibold text-sm transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 [&:not(:disabled)]:hover:cursor-pointer [&:not(:disabled)]:hover:brightness-110 [&:not(:disabled)]:active:scale-[0.98]'
  const variant =
    props.type === 'secondary'
      ? 'bg-btn-secondary text-white focus:ring-btn-secondary disabled:opacity-50 disabled:cursor-not-allowed'
      : 'bg-btn-primary text-white focus:ring-btn-primary disabled:opacity-50 disabled:cursor-not-allowed'

  return (
    <button
      className={`${base} ${variant}`}
      onClick={props.onClick}
      disabled={props.disabled}
    >
      {props.children}
    </button>
  )
}
