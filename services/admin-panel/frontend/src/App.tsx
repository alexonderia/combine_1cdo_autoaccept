import { useCallback, useState } from 'react';
import { AppHeader } from './components/layout/AppHeader';
import { Modal } from './components/ui/Modal';
import { useLazyResource } from './core/hooks/useLazyResource';
import type { ConfigService, PromptDraft, PromptService, Service } from './core/types';
import { ConfigPanel } from './features/config/components/ConfigPanel';
import { fetchConfigServices } from './features/config/api';
import { PromptList } from './features/prompts/components/PromptList';
import { fetchPromptServices, updatePrompt } from './features/prompts/api';
import { ProxyTester } from './features/proxy/components/ProxyTester';
import { ServiceStatusPanel } from './features/services/components/ServiceStatusPanel';
import { fetchServiceStatus } from './features/services/api';
import type { TabKey } from './types/tabs';

const DEFAULT_PROMPTS: PromptService[] = [];
const DEFAULT_SERVICES: Service[] = [];
const DEFAULT_CONFIG: ConfigService[] = [];

function App() {
  const [currentTab, setCurrentTab] = useState<TabKey>('services');
  const [editingPrompt, setEditingPrompt] = useState<PromptDraft | null>(null);
  const [isModalOpen, setModalOpen] = useState(false);

  const servicesResource = useLazyResource(fetchServiceStatus, {
    initialValue: DEFAULT_SERVICES,
    isActive: currentTab === 'services',
  });

  const promptResource = useLazyResource(fetchPromptServices, {
    initialValue: DEFAULT_PROMPTS,
    isActive: currentTab === 'prompts',
  });

  const configResource = useLazyResource(fetchConfigServices, {
    initialValue: DEFAULT_CONFIG,
    isActive: currentTab === 'config',
  });

  const handleEditPrompt = useCallback((service: string, name: string, content: string) => {
    setEditingPrompt({ service, name, content });
    setModalOpen(true);
  }, []);

  const handleSavePrompt = useCallback(async () => {
    if (!editingPrompt) return;

    await updatePrompt(editingPrompt);
    await promptResource.refresh();
    setModalOpen(false);
  }, [editingPrompt, promptResource]);

  return (
    <>
      <AppHeader currentTab={currentTab} onChangeTab={setCurrentTab} />
      <main className="main-content">
        {currentTab === 'services' && (
          <ServiceStatusPanel
            services={servicesResource.data}
            onRefresh={servicesResource.refresh}
            loading={servicesResource.loading}
          />
        )}
        {currentTab === 'prompts' && (
          <PromptList promptServices={promptResource.data} onEdit={handleEditPrompt} />
        )}
        {currentTab === 'config' && (
          <ConfigPanel
            configServices={configResource.data}
            onRefresh={configResource.refresh}
            loading={configResource.loading}
          />
        )}
        {currentTab === 'proxyTester' && <ProxyTester />}
      </main>

      {isModalOpen && editingPrompt && (
        <Modal title="Редактирование промпта" onClose={() => setModalOpen(false)} onSave={handleSavePrompt}>
          <p>
            <strong>Сервис:</strong> {editingPrompt.service}
          </p>
          <p>
            <strong>Файл:</strong> {editingPrompt.name}
          </p>
          <textarea
            value={editingPrompt.content}
            onChange={(event) => setEditingPrompt({ ...editingPrompt, content: event.target.value })}
          />
        </Modal>
      )}
    </>
  );
}

export default App;
