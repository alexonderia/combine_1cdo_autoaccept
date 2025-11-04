import type { ReactNode } from 'react';

export interface ModalProps {
  title: string;
  children: ReactNode;
  onClose: () => void;
  onSave: () => void;
}

/**
 * Reusable modal dialog with confirmation buttons.
 */
export function Modal({ title, children, onClose, onSave }: ModalProps) {
  return (
    <div className="modal">
      <div className="modal-content">
        <h3>{title}</h3>
        {children}
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose} type="button">
            Отмена
          </button>
          <button className="btn btn-primary" onClick={onSave} type="button">
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );
}
