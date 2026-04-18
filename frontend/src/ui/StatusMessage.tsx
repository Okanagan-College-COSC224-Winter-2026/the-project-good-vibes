interface Props {
  message?: string | null;
  type?: 'error' | 'success';
  className?: string;
  children?: React.ReactNode;
}

export default function StatusMessage(props: Props) {
  const type = props.type || 'error';

  if (!props.message && !props.children) {
    return null;
  }

  const typeClasses =
    type === 'success'
      ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
      : 'bg-red-50 border-red-200 text-red-700'

  return (
    <div
      className={`flex items-center gap-2 px-4 py-3 mb-4 rounded-lg text-sm border ${typeClasses} ${props.className ?? ''}`}
      role="alert"
      aria-live="polite"
    >
      {props.children ? props.children : <span className="flex-1">{props.message}</span>}
    </div>
  );
}
