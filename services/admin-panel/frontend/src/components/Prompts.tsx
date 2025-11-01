import type { PromptService } from "../models/types";

type Props = {
  promptServices: PromptService[];
  onEdit: (service: string, name: string, content: string) => void;
};

export const Prompts = ({ promptServices, onEdit }: Props) => {
  

  return (
    <div className="card">
      <h2>Управление промптами</h2>
      <div className="prompts-list">
        {promptServices.map((service) => (
          <div key={service.name} className="service-section">
            <h3>{service.name}</h3>
            {service.prompts.map((prompt) => (
              <div key={prompt.name} className="prompt-item">
                <span className="prompt-name">{prompt.name}</span>
                <button
                  className="btn-link"
                  onClick={() =>
                    onEdit(service.name, prompt.name, prompt.content)
                  }
                >
                  Редактировать
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
