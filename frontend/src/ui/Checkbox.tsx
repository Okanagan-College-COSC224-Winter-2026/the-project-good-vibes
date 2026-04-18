interface Props {
  id?: string;
  name?: string;
  checked: boolean;
  onChange: () => void;
  label?: string;
  className?: string;
}

export default function Checkbox(props: Props) {
  return (
    <label className={`inline-flex items-center gap-2 cursor-pointer select-none text-[0.95rem] ${props.className || ''}`}>
      <input
        id={props.id}
        name={props.name}
        type="checkbox"
        checked={props.checked}
        onChange={props.onChange}
        className="w-4 h-4 cursor-pointer"
      />
      <span>{props.label}</span>
    </label>
  );
}
