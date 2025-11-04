import type { ConfigService } from '../../../core/types';

export interface ConfigPanelProps {
  configServices: ConfigService[];
  onRefresh: () => void;
  loading: boolean;
}

/**
 * Shows configuration key-value pairs retrieved from backend services.
 */
export function ConfigPanel({ configServices, onRefresh, loading }: ConfigPanelProps) {
  return (
    <div className="card">
      <div className="card-header">
        <h2>Конфигурация сервисов</h2>
        <button className="btn btn-primary" onClick={onRefresh} disabled={loading} type="button">
          {loading ? 'Обновление...' : 'Обновить конфигурацию'}
        </button>
      </div>

      <div className="config-grid">
        {configServices.map((service) => (
          <div key={service.name} className="service-section">
            <h3>{service.name}</h3>
            {Object.entries(service.config).map(([key, value]) => (
              <div key={key} className="config-item">
                <span className="config-key">{key}</span>
                <span className="config-value">{value}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
