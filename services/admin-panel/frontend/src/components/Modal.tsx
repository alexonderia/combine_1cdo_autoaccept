type Props = {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  onSave: () => void;
};

export const Modal = ({ title, children, onClose, onSave }: Props) => {
  return (
    <div className="modal">
      <div className="modal-content">
        <h3>{title}</h3>
        {children}
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>
            Отмена
          </button>
          <button className="btn btn-primary" onClick={onSave}>
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );
}
