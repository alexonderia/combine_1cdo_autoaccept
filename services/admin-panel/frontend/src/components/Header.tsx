type Props = {
  currentTab: string;
  setCurrentTab: (tab: "services" | "prompts" | "config" | "proxyTester") => void;
};

export const Header = ({ currentTab, setCurrentTab }: Props) => {
  return (
    <header className="header">
      <div className="header-content">
        <h1>Admin Panel</h1>
        <div className="nav-tabs">
          <button
            className={currentTab === "services" ? "nav-tab active" : "nav-tab"}
            onClick={() => setCurrentTab("services")}
          >
            Сервисы
          </button>
          <button
            className={currentTab === "prompts" ? "nav-tab active" : "nav-tab"}
            onClick={() => setCurrentTab("prompts")}
          >
            Промпты
          </button>
          <button
            className={currentTab === "config" ? "nav-tab active" : "nav-tab"}
            onClick={() => setCurrentTab("config")}
          >
            Конфигурация
          </button>
          <button
            className={currentTab === "proxyTester" ? "nav-tab active" : "nav-tab"}
            onClick={() => setCurrentTab("proxyTester")}
          >
            Тестирование запросов
          </button>
        </div>
      </div>
    </header>
  );
}
