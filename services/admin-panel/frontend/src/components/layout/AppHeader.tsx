import type { TabKey } from '../../types/tabs';

export interface AppHeaderProps {
  currentTab: TabKey;
  onChangeTab: (tab: TabKey) => void;
}

/**
 * Top navigation bar that allows switching between application sections.
 */
export function AppHeader({ currentTab, onChangeTab }: AppHeaderProps) {
  const renderTabButton = (tab: TabKey, label: string) => (
    <button
      key={tab}
      className={currentTab === tab ? 'nav-tab active' : 'nav-tab'}
      onClick={() => onChangeTab(tab)}
      type="button"
    >
      {label}
    </button>
  );

  return (
    <header className="header">
      <div className="header-content">
        <h1>Admin Panel</h1>
        <div className="nav-tabs">
          {renderTabButton('services', 'Сервисы')}
          {renderTabButton('prompts', 'Промпты')}
          {renderTabButton('config', 'Конфигурация')}
          {renderTabButton('proxyTester', 'Тестирование запросов')}
        </div>
      </div>
    </header>
  );
}
