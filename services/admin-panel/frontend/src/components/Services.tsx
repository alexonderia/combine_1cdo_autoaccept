import type { Service } from "../models/types";

type Props = {
  services: Service[];
  onRefresh: () => void;
};

export const Services = ({ services, onRefresh }: Props) => {
  const getStatusClass = (status: string) => {
    switch (status) {
      case "ok":
        return "status-ok";
      case "error":
        return "status-error";
      case "down":
        return "status-down";
      default:
        return "status-error";
    }
  };

  return (
    <div className="card">
      <h2>Статус сервисов</h2>
      <div className="services-grid">
        {services.map((s) => (
          <div key={s.name} className="service-card">
            <div className="service-header">
              <h3>{s.name}</h3>
              <span className={`status-badge ${getStatusClass(s.status)}`}>
                {s.status}
              </span>
            </div>
            <div className="service-details">
              <p>URL: {s.url}</p>
              <p>Версия: {s.version || "N/A"}</p>
              {s.details &&
                Object.entries(s.details).map(([k, v]) => (
                  <p key={k}>
                    {k}: {v}
                  </p>
                ))}
            </div>
          </div>
        ))}
      </div>
      <button className="btn btn-primary" onClick={onRefresh}>
        Обновить статус
      </button>
    </div>
  );
}
