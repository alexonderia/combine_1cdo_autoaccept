import type { ConfigService } from "../models/types";

type Props = {
    configServices: ConfigService[];
    onRefresh: () => void;
};

export const Config = ({ configServices, onRefresh }: Props) => {
    return (
        <div className="card">
            <h2>Конфигурация сервисов</h2>

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
            <br></br>
            <button className="btn btn-primary" onClick={onRefresh}>
                Обновить конфигурацию
            </button>
        </div>
    );
}
