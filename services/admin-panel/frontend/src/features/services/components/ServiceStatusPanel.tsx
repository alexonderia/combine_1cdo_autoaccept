import type { Service } from '../../../core/types';

export interface ServiceStatusPanelProps {
  services: Service[];
  onRefresh: () => void;
  loading: boolean;
}

/**
 * Displays the current health status of backend services.
 */
export function ServiceStatusPanel({ services, onRefresh, loading }: ServiceStatusPanelProps) {
  const getStatusClass = (status: string) => {
    switch (status) {
      case 'ok':
        return 'status-ok';
      case 'error':
        return 'status-error';
      case 'down':
        return 'status-down';
      default:
        return 'status-error';
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Статус сервисов</h2>
        <button className="btn btn-primary" onClick={onRefresh} disabled={loading} type="button">
          {loading ? 'Обновление...' : 'Обновить статус'}
        </button>
      </div>

      <div className="services-grid">
        {services.map((service) => (
          <div key={service.name} className="service-card">
            <div className="service-header">
              <h3>{service.name}</h3>
              <span className={`status-badge ${getStatusClass(service.status)}`}>
                {service.status}
              </span>
            </div>
            <div className="service-details">
              <p>URL: {service.url}</p>
              <p>Версия: {service.version ?? 'N/A'}</p>
              {service.details &&
                Object.entries(service.details).map(([key, value]) => (
                  <p key={key}>
                    {key}: {value}
                  </p>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
