import { ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

export default function Modal({ isOpen, onClose, title, children }: ModalProps) {
  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex justify-center items-center z-[1000] p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto modal-slide-in border border-border">
        <div className="flex justify-between items-center px-6 py-4 border-b border-border gap-4">
          <h2 className="m-0 text-lg font-semibold text-text-primary flex-1">{title}</h2>
          <button
            className="bg-transparent border-none text-lg text-text-secondary cursor-pointer p-0 w-8 h-8 flex items-center justify-center rounded-lg transition-colors hover:bg-bg-secondary hover:text-text-primary"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>
        <div className="px-6 py-5 flex flex-col gap-4 [&>label]:flex [&>label]:flex-col [&>label]:gap-1.5 [&>label]:text-text-primary [&>label]:text-sm [&>label]:font-medium [&_input]:px-3 [&_input]:py-2 [&_input]:border [&_input]:border-border [&_input]:rounded-lg [&_input]:bg-bg-secondary [&_input]:text-text-primary [&_input]:font-[inherit] [&_textarea]:px-3 [&_textarea]:py-2 [&_textarea]:border [&_textarea]:border-border [&_textarea]:rounded-lg [&_textarea]:bg-bg-secondary [&_textarea]:text-text-primary [&_textarea]:font-[inherit]">
          {children}
        </div>
      </div>
    </div>
  );
}
