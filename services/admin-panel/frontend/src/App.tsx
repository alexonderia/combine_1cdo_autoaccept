
import { Header } from './components/Header'
import { useEffect, useState } from 'react';
import { fetchConfig, fetchPrompts, fetchServices, updatePrompt } from './api';
import type { Service, PromptService, ConfigService} from './models/types';
import { Services } from './components/Services';
import { Prompts } from './components/Prompts';
import { Config } from './components/Config';
import { Modal } from './components/Modal';
import { ProxyTester } from './components/ProxyTester';

function App() {
  const [currentTab, setCurrentTab] = useState<"services" | "prompts" | "config" | "proxyTester">("services");
  const [services, setServices] = useState<Service[]>([]);
  const [configServices, setConfigServices] = useState<ConfigService[]>([]);
  const [promptServices, setPromptServices] = useState<PromptService[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<{
    service: string;
    name: string;
    content: string;
  } | null>(null);
  const loadData = async () => {
    try {
      const srv = await fetchServices();
      setServices(srv);
    } catch (err) {
      console.error("Ошибка загрузки данных:", err);
    }
  };

  const loadPrompts = async () => {
    try {
      const data = await fetchPrompts();
      setPromptServices(data);
    } catch (err) {
      console.error("Ошибка загрузки промптов:", err);
    }
  };

  const loadConfig = async () => {
    try {
      const data = await fetchConfig();
      setConfigServices(data);
    } catch (err) {
      console.error("Ошибка загрузки конфигурации:", err);
    }
  };


  useEffect(() => {
    if (currentTab === "services") loadData();
    if (currentTab === "prompts") loadPrompts();
    if (currentTab === "config") loadConfig();
  }, [currentTab]);

  const handleEditPrompt = (service: string, name: string, content: string) => {
    setEditingPrompt({ service, name, content });
    setShowModal(true);
  };

  const handleSavePrompt = async () => {
    if (!editingPrompt) return;
    const ok = await updatePrompt(editingPrompt);
    if (ok) {
      
      alert("Промт успешно обновлен");
      setShowModal(false);
      loadPrompts(); // обновляем список промтов
    } else {
      alert("Ошибка при сохранении промта");
    }
  };

  return (
    <>
      <Header currentTab={currentTab} setCurrentTab={setCurrentTab} />
      <main className="main-content">
        {currentTab === "services" && (
          <Services services={services} onRefresh={loadData} />
        )}
        {currentTab === "prompts" && (
          <Prompts promptServices={promptServices} onEdit={handleEditPrompt} />
        )}
        {currentTab === "config" && (
          <Config configServices={configServices} onRefresh={loadConfig} />
        )}
        {currentTab === "proxyTester" && (
          <ProxyTester />
        )}
      </main>

      {showModal && editingPrompt && (
        <Modal
          title="Редактирование промпта"
          onClose={() => setShowModal(false)}
          onSave={handleSavePrompt}
        >
          <p>
            <strong>Сервис:</strong> {editingPrompt.service}
          </p>
          <p>
            <strong>Файл:</strong> {editingPrompt.name}
          </p>
          <textarea
            value={editingPrompt.content}
            onChange={(e) =>
              setEditingPrompt({ ...editingPrompt, content: e.target.value })
            }
          />
        </Modal>
      )}
    </>
  )
}

export default App
