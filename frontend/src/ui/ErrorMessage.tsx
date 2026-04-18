interface Props {
  message?: string | null;
  className?: string;
}

export default function ErrorMessage(props: Props) {
  return (
    <div className={`flex items-center gap-2 px-4 py-3 mb-4 bg-[#fee] border border-[#fcc] rounded text-[#c33] text-[0.95rem] ${props.className ?? ''}`}>
      <span className="flex-1">{props.message}</span>
    </div>
  );
}
